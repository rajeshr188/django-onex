from decimal import Decimal

from django.db import models
from django.db.models import OuterRef, Subquery, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import reverse

from dea.models import Journal
from utils.friendlyid import encode

from ..managers import StockLotManager, StockManager


class Stock(models.Model):

    """
    represents stock for each product variant.this stock is used in sale/purchase purposes
    """

    created = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    reorderat = models.IntegerField(default=1)

    variant = models.ForeignKey(
        "product.ProductVariant", on_delete=models.CASCADE, related_name="stocks"
    )

    objects = StockManager()

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        cb = self.current_balance()
        return f"{self.variant} {cb['wt']} {cb['qty']}"

    def get_absolute_url(self):
        return reverse("product_stock_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("product_stock_update", args=(self.pk,))

    def get_pure_by_melting(self):
        bal = self.current_balance()
        return bal["wt"] * self.melting

    def get_pure_by_cost(self):
        bal = self.current_balance()
        return bal["wt"] * self.cost

    def audit(self):
        """
        get last audit cb,totalin,total out and then append following
        """
        try:
            last_statement = self.stockstatement_set.latest()
        except StockStatement.DoesNotExist:
            last_statement = None
        if last_statement is not None:
            ls_wt = last_statement.Closing_wt
            ls_qty = last_statement.Closing_qty
        else:
            ls_wt = 0
            ls_qty = 0

        stock_in = self.stock_in_txns(last_statement)
        stock_out = self.stock_out_txns(last_statement)
        cb_wt = ls_wt + (stock_in["wt"] - stock_out["wt"])
        cb_qty = ls_qty + (stock_in["qty"] - stock_out["qty"])

        return StockStatement.objects.create(
            stock=self,
            Closing_wt=cb_wt,
            Closing_qty=cb_qty,
            total_wt_in=stock_in["wt"],
            total_qty_in=stock_in["qty"],
            total_wt_out=stock_out["wt"],
            total_qty_out=stock_out["qty"],
        )

    def stock_in_txns(self, ls):
        """
        return all the In transactions since last audit"""
        st = self.stocktransaction_set.all()
        if ls:
            st = st.filter(created__gte=ls.created)
        st = st.filter(movement_type__in=["P", "SR", "AR", "AD", "IN"])

        return st.aggregate(
            qty=Coalesce(models.Sum("quantity", output_field=models.IntegerField()), 0),
            wt=Coalesce(
                models.Sum("weight", output_field=models.DecimalField()), Decimal(0.0)
            ),
        )

    def stock_out_txns(self, ls):
        """
        return all Out Transactions since last audit
        """
        st = self.stocktransaction_set.all()
        if ls:
            st = st.filter(created__gte=ls.created)
        st = st.filter(movement_type__in=["PR", "S", "A", "RM", "OT"])

        return st.aggregate(
            qty=Coalesce(models.Sum("quantity", output_field=models.IntegerField()), 0),
            wt=Coalesce(
                models.Sum("weight", output_field=models.DecimalField()), Decimal(0.0)
            ),
        )

    def current_balance(self):
        """
        compute balance from last audit and append following
        """
        bal = {}
        Closing_wt: Decimal = 0
        Closing_qty: int = 0

        try:
            ls = self.stockstatement_set.latest()
            Closing_wt = ls.Closing_wt
            Closing_qty = ls.Closing_qty

        except StockStatement.DoesNotExist:
            ls = None

        in_txns = self.stock_in_txns(ls)
        out_txns = self.stock_out_txns(ls)
        bal["wt"] = Closing_wt + (in_txns["wt"] - out_txns["wt"])
        bal["qty"] = Closing_qty + (in_txns["qty"] - out_txns["qty"])
        return bal

    # def get_age(self):
    #     """
    #     returns age of stock in days
    #     """
    #     return (self.created - self.updated_on).days

    def transact(self, weight, quantity, journal, movement_type):
        """
        Modifies weight and quantity associated with the stock based on movement type
        Returns none
        """
        StockTransaction.objects.create(
            journal=journal,
            stock=self,
            weight=weight,
            quantity=quantity,
            movement_type_id=movement_type,
        )
        self.update_status()

    def merge_lots(self):
        """
        merges all lots in to individual lots representing this stock of its product variant.
        single operation to merge lots blindly.
        merge only non huid/non-unique lots

        """
        all_lots = self.lots.exclude(is_unique=True)
        current = all_lots.current_balance()
        new_lot = StockLot.objects.create(
            wt=current.wt, qty=current.qty, stock=current.stock
        )
        new_lot.transact(
            wt=current.wt, qty=current.qty, journal=None, movement_type="AD"
        )
        for i in all_lots:
            i.transact(wt=current.wt, qty=current.qty, journal=None, movement_type="RM")
        return new_lot


class StockLot(models.Model):
    """
    StockLot core idea:
        1 productV has many lots and all lots[productv] reference one stock
        on purchase add to stocklot from purchase_item
        on sale choose from stocklot from sale_item
        a lot belongs to a purchase and can be split/merged into new lot belonging to same purchase
        smaller lots can be stockout'ed and stockin'ed seperately
    """

    # should this be mptt?Maybe

    created = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    quantity = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=3)
    barcode = models.CharField(
        max_length=155, null=True, blank=True, unique=True, editable=False
    )
    huid = models.CharField(max_length=6, null=True, blank=True, unique=True)
    stock_code = models.CharField(max_length=4, blank=True, null=True)
    purchase_touch = models.DecimalField(max_digits=10, decimal_places=3)
    purchase_rate = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True
    )
    is_unique = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10,
        choices=(
            ("Empty", "Empty"),
            ("Available", "Available"),
            ("Sold", "Sold"),
            ("Approval", "Approval"),
            ("Return", "Return"),
        ),
        default="Empty",
    )

    # related fields
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="lots")
    # redundant aint it?
    variant = models.ForeignKey(
        "product.ProductVariant", on_delete=models.CASCADE, related_name="stock_lots"
    )

    purchase_item = models.ForeignKey(
        "purchase.InvoiceItem",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="item_lots",
    )

    objects = StockLotManager()

    def __str__(self):
        return (
            f"{self.barcode} | {self.huid or ''} | {self.variant} | {self.current_balance()}"
        )

    @classmethod
    def with_balance(cls):
        balance_subquery = (
            StockLotBalance.objects.filter(stocklot_id=OuterRef("pk"))
            .values("stocklot_id")
            .annotate(total_balance=Coalesce(Sum("balance"), 0))
            .values("total_balance")
        )
        queryset = cls.objects.annotate(balance=Subquery(balance_subquery))
        return queryset

    def generate_barcode(self):
        print("generating barcode")
        if not self.barcode:
            self.barcode = encode(self.pk)
            self.save()

    def update_status(self):
        cb = self.current_balance()
        if cb["wt"] <= 0.0 or cb["qty"] <= 0:
            self.status = "Empty"
        else:
            self.status = "Available"
        self.save()

    def audit(self):
        try:
            last_statement = self.stockstatement_set.latest()
        except StockStatement.DoesNotExist:
            last_statement = None

        if last_statement is not None:
            ls_wt = last_statement.Closing_wt
            ls_qty = last_statement.Closing_qty
        else:
            ls_wt = 0
            ls_qty = 0

        stock_in = self.stock_in_txns(last_statement)
        stock_out = self.stock_out_txns(last_statement)
        cb_wt = ls_wt + (stock_in["wt"] - stock_out["wt"])
        cb_qty = ls_qty + (stock_in["qty"] - stock_out["qty"])

        return StockStatement.objects.create(
            stock=self.stock,
            stock_batch=self,
            Closing_wt=cb_wt,
            Closing_qty=cb_qty,
            total_wt_in=stock_in["wt"] if stock_in["wt"] else 0.0,
            total_qty_in=stock_in["qty"] if stock_in["qty"] else 0,
            total_wt_out=stock_out["wt"] if stock_out["wt"] else 0.0,
            total_qty_out=stock_out["qty"] if stock_out["qty"] else 0,
        )

    def stock_in_txns(self, ls):
        # filter since last audit
        st = self.stocktransaction_set.all()
        if ls:
            st = st.filter(created__gte=ls.created)
        st = st.filter(movement_type__id__in=["P", "SR", "AR", "AD", "IN"])

        return st.aggregate(
            qty=Coalesce(models.Sum("quantity", output_field=models.IntegerField()), 0),
            wt=Coalesce(
                models.Sum("weight", output_field=models.DecimalField()), Decimal(0.0)
            ),
        )

    def stock_out_txns(self, ls):
        # filter since last audit
        st = self.stocktransaction_set.all()
        if ls:
            st = st.filter(created__gte=ls.created)
        st = st.filter(movement_type__id__in=["PR", "S", "A", "RM", "OT"])

        return st.aggregate(
            qty=Coalesce(models.Sum("quantity", output_field=models.IntegerField()), 0),
            wt=Coalesce(
                models.Sum("weight", output_field=models.DecimalField()), Decimal(0.0)
            ),
        )

    def current_balance(self):
        # compute cb from last audit and append following
        bal = {}
        try:
            ls = self.stockstatement_set.latest()
            Closing_wt = ls.Closing_wt
            Closing_qty = ls.Closing_qty
        except StockStatement.DoesNotExist:
            ls = None
            Closing_wt = 0
            Closing_qty = 0
        in_txns = self.stock_in_txns(ls)
        out_txns = self.stock_out_txns(ls)
        bal["wt"] = Closing_wt + (in_txns["wt"] - out_txns["wt"])
        bal["qty"] = Closing_qty + (in_txns["qty"] - out_txns["qty"])
        return bal
    
    def get_total_sold(self):
        return self.sold_items.aggregate(
            qty=Coalesce(models.Sum("quantity", output_field=models.IntegerField()), 0),
            wt=Coalesce(
                models.Sum("weight", output_field=models.DecimalField()), Decimal(0.0)
            ),
        )

    def transact(self, weight, quantity, journal, movement_type):
        """
        Modifies weight and quantity associated with the stock based on movement type
        Returns none
        """
        StockTransaction.objects.create(
            journal=journal,
            lot=self,
            weight=weight,
            quantity=quantity,
            movement_type_id=movement_type,
            stock=self.stock,
        )
        self.update_status()

    def merge(self, lot: int):
        """
        a lots qty and weight remains same troughout its life,
        any add/remove/merge/split on a lot is performed via transactions,
        and current balance of a lot is derived from transaction.

        Return : new_lot:StockLot
        """

        if self.variant != lot.variant or self.stock != lot.stock:
            raise Exception(
                "cannot merge lots from different variant or associated with different stock"
            )

        new_lot = StockLot(
            variant=self.variant,
            weight=lot.weight + self.eight,
            quantity=lot.quantity + self.quantity,
        )
        self.transact(self.weight, self.quantity, journal=None, movement_type="RM")
        lot.transact(lot.weight, lot.quantity, journal=None, movement_type="RM")
        new_lot.transact(
            self.weight + lot.weight,
            self.quantity + lot.quantity,
            journal=None,
            movement_type="AD",
        )
        return new_lot

    def split(self, wt: Decimal, qty: int):
        """
        split a lot by creating a new lot and transfering the wt & qty to new lot
        """
        if not self.is_unique and self.quantity > qty and self.weight > wt:
            new_lot = StockLot(variant=self.variant, weight=wt, quantity=qty)
            new_lot.transact(wt, qty, journal=None, movement_type="AD")

            self.transact(wt, qty, journal=None, movement_type="RM")

            return new_lot
        raise Exception("Unique lots cant be split")

    def get_age(self):
        return (timezone.now() - self.created).days


class Movement(models.Model):

    """represents movement_type with direction of stock/lot transaction
    ex: [('purchase','+'),('purchase return','-'),('sales','-'),('sale return','+'),
        ('split','-'),('merge','+')]
    """

    id = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=30)
    direction = models.CharField(max_length=1, default="+")


class StockTransaction(models.Model):
    created = models.DateTimeField(auto_now_add=True)

    quantity = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    description = models.TextField()

    # relational Fields
    # user = models.ForeignKey(CustomUser)
    movement_type = models.ForeignKey(Movement, on_delete=models.CASCADE, default="P")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    lot = models.ForeignKey(StockLot, on_delete=models.CASCADE, default=1)

    journal = models.ForeignKey(Journal, on_delete=models.CASCADE, related_name="stxns")

    class Meta:
        ordering = ("-created",)
        get_latest_by = ["created"]

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse("product_stocktransaction_detail", args=(self.pk,))

    def get_update_url(self):
        return reverse("product_stocktransaction_update", args=(self.pk,))


class StockStatement(models.Model):
    ss_method = (
        ("Auto", "Auto"),
        ("Physical", "Physical"),
    )
    method = models.CharField(max_length=20, choices=ss_method, default="Auto")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    lot = models.ForeignKey(StockLot, on_delete=models.CASCADE, null=True)

    created = models.DateTimeField(auto_now=True)
    Closing_wt = models.DecimalField(max_digits=14, decimal_places=3)
    Closing_qty = models.IntegerField()
    total_wt_in = models.DecimalField(max_digits=14, decimal_places=3, default=0.0)
    total_wt_out = models.DecimalField(max_digits=14, decimal_places=3, default=0.0)
    total_qty_in = models.IntegerField(default=0.0)
    total_qty_out = models.IntegerField(default=0.0)

    class Meta:
        ordering = ("created",)
        get_latest_by = ["created"]

    def __str__(self):
        return f"{self.stock} - qty:{self.Closing_qty} wt:{self.Closing_wt}"


class StockBalance(models.Model):
    stock = models.OneToOneField(Stock, on_delete=models.DO_NOTHING, primary_key=True)
    Closing_wt = models.DecimalField(max_digits=14, decimal_places=3)
    Closing_qty = models.IntegerField()
    in_wt = models.DecimalField(max_digits=14, decimal_places=3)
    in_qty = models.IntegerField()
    out_wt = models.DecimalField(max_digits=14, decimal_places=3)
    out_qty = models.IntegerField()

    class Meta:
        managed = False
        db_table = "stock_balance"

    def get_qty_bal(self):
        return self.Closing_qty + self.in_qty - self.out_qty

    def get_wt_bal(self):
        return self.Closing_wt + self.in_wt - self.out_wt


class StockLotBalance(models.Model):
    lot = models.OneToOneField(StockLot, on_delete=models.DO_NOTHING, primary_key=True)
    Closing_wt = models.DecimalField(max_digits=14, decimal_places=3)
    Closing_qty = models.IntegerField()
    in_wt = models.DecimalField(max_digits=14, decimal_places=3, default=0.0)
    in_qty = models.IntegerField(default=0)
    out_wt = models.DecimalField(max_digits=14, decimal_places=3, default=0.0)
    out_qty = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = "stockbatch_balance"

    def get_qty_bal(self):
        return self.Closing_qty + self.in_qty - self.out_qty

    def get_wt_bal(self):
        return self.Closing_wt + self.in_wt - self.out_wt
