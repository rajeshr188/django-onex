# Generated by Django 4.2.3 on 2023-07-23 11:17


import mptt
import mptt.managers
from django.db import migrations


def rebuild_category(apps, schema_editor):
    manager = mptt.managers.TreeManager()
    Category = apps.get_model("product", "Category")
    manager.model = Category
    mptt.register(Category, order_insertion_by=["name"])
    manager.contribute_to_class(Category, "objects")
    manager.rebuild()


def noop_reverse(apps, schema_editor):
    pass


def insertData(apps, schema_editor):
    category = apps.get_model("product", "Category")
    category.objects.create(name="Gold", lft=0, rght=0, level=0, tree_id=0)
    category.objects.create(name="Silver", lft=0, rght=0, level=0, tree_id=0)

    product_type = apps.get_model("product", "ProductType")
    product_type.objects.bulk_create(
        [
            product_type(name="Coin"),
            product_type(name="Kalkass"),
            product_type(name="Drops"),
            product_type(name="Ring"),
            product_type(name="Haram"),
            product_type(name="Necklace"),
            product_type(name="Chain"),
            product_type(name="Choker"),
            product_type(name="Dollar"),
            product_type(name="Taali"),
            product_type(name="Gundu"),
            product_type(name="Thirupadam"),
            product_type(name="Urupadi"),
            product_type(name="Chippe Stone"),
            product_type(name="Mattal"),
            product_type(name="Moppu"),
            product_type(name="Minimattal"),
            product_type(name="Crystal tongal"),
            product_type(name="Jhapka"),
            product_type(name="Mangtika"),
            product_type(name="Jhapka Mattal"),
            product_type(name="Neckchain"),
            product_type(name="Pendants"),
            product_type(name="Bracelet"),
            product_type(name="Kamal"),
            product_type(name="Kamal Jumki"),
            product_type(name="Stud"),
        ]
    )
    attribute = apps.get_model("product", "Attribute")
    attribute.objects.bulk_create(
        [
            attribute(name="Purity", slug="purity"),
            attribute(name="Design", slug="design"),
            attribute(name="Size", slug="size"),
            attribute(name="Length", slug="length"),
            attribute(name="Gender", slug="gender"),
            attribute(name="Weight", slug="weight"),
            attribute(name="Initial", slug="initial"),
        ]
    )
    movement_type = apps.get_model("product", "movement")
    movement_type.objects.bulk_create(
        [
            movement_type(id="P", name="Purchase", direction="+"),
            movement_type(id="PR", name="Purchase Return", direction="-"),
            movement_type(id="S", name="Sales", direction="-"),
            movement_type(id="SR", name="Sales Return", direction="+"),
            movement_type(id="A", name="Approval", direction="-"),
            movement_type(id="AR", name="Approval Return", direction="+"),
            movement_type(id="AD", name="Add", direction="+"),
            movement_type(id="R", name="Remove", direction="-"),
        ]
    )
    attrvalue = apps.get_model("product", "AttributeValue")
    attrvalue.objects.bulk_create(
        [
            attrvalue(attribute_id=1, name="999", value="999", slug="999"),
            attrvalue(attribute_id=1, name="916", value="916", slug="916"),
            attrvalue(attribute_id=1, name="84", value="84", slug="84"),
            attrvalue(attribute_id=1, name="80", value="80", slug="80"),
            attrvalue(attribute_id=1, name="75", value="75", slug="75"),
            attrvalue(attribute_id=2, name="Cbe", value="Cbe", slug="CB"),
            attrvalue(attribute_id=2, name="Bombay", value="Bmby", slug="Bmby"),
            attrvalue(attribute_id=2, name="Dilli", value="Dilli", slug="Dilli"),
            attrvalue(attribute_id=2, name="Kasha", value="Kasha", slug="Kasha"),
            attrvalue(attribute_id=2, name="Varika", value="varika", slug="varika"),
            attrvalue(attribute_id=2, name="Kerala", value="Kerala", slug="Kerala"),
            attrvalue(attribute_id=2, name="Goduma Cutting", value="gc", slug="gc"),
            attrvalue(attribute_id=2, name="Tyre Cut", value="tc", slug="tc"),
            attrvalue(attribute_id=2, name="Hollow Rope", value="hr", slug="hr"),
            attrvalue(attribute_id=2, name="Square Rope", value="sr", slug="sr"),
            attrvalue(attribute_id=2, name="Sundari", value="Sundari", slug="sundari"),
            attrvalue(attribute_id=2, name="Lotus", value="lotus", slug="lotus"),
            attrvalue(attribute_id=2, name="IPL", value="ipl", slug="ipl"),
            attrvalue(attribute_id=2, name="Leaf", value="leaf", slug="leaf"),
            attrvalue(attribute_id=2, name="Uthapa", value="uthapa", slug="uthapa"),
            attrvalue(attribute_id=2, name="Sleaf", value="sleaf", slug="sleaf"),
            attrvalue(
                attribute_id=2, name="Heartnleaf", value="heartnleaf", slug="heartnleaf"
            ),
            attrvalue(
                attribute_id=2, name="Singapore", value="singapore", slug="singapore"
            ),
            attrvalue(
                attribute_id=2,
                name="Moppu Sundari ",
                value="moppu sundari",
                slug="moppusundari",
            ),
            attrvalue(attribute_id=2, name="Nawabi", value="nawabi", slug="nawabi"),
            attrvalue(
                attribute_id=2, name="Bahubali", value="bahubali", slug="bahubali"
            ),
            attrvalue(attribute_id=2, name="Super Lotus", value="Lotus", slug="Lotus"),
            attrvalue(attribute_id=2, name="Plate", value="Plate", slug="Plate"),
            attrvalue(attribute_id=2, name="Round", value="Round", slug="Round"),
            attrvalue(attribute_id=2, name="TV", value="tv", slug="tv"),
            attrvalue(attribute_id=2, name="Vanki", value="vanki", slug="vanki"),
            attrvalue(attribute_id=2, name="Basha", value="basha", slug="basha"),
            attrvalue(
                attribute_id=2, name="Tendulkar", value="tendulkar", slug="tendulkar"
            ),
            attrvalue(attribute_id=2, name="focus", value="focus", slug="focus"),
            attrvalue(attribute_id=2, name="Jallar", value="jallar", slug="jallar"),
            attrvalue(attribute_id=2, name="Enamel", value="enamel", slug="enamel"),
            attrvalue(attribute_id=2, name="Nellika", value="nellika", slug="nellika"),
            attrvalue(attribute_id=2, name="Patte", value="patte", slug="patte"),
            attrvalue(attribute_id=2, name="Lakshmi", value="lakshmi", slug="lakshmi"),
            attrvalue(
                attribute_id=2, name="Christian", value="christian", slug="christian"
            ),
            attrvalue(attribute_id=2, name="Lion", value="lion", slug="lion"),
            attrvalue(attribute_id=2, name="Peacock", value="peacock", slug="peacock"),
            attrvalue(
                attribute_id=2, name="Yannamudi", value="yanamudi", slug="yanamudi"
            ),
            attrvalue(attribute_id=2, name="pondy", value="pondy", slug="pondy"),
            attrvalue(attribute_id=3, name="2.2", value="2.2", slug="2.2"),
            attrvalue(attribute_id=3, name="2.3", value="2.3", slug="2.3"),
            attrvalue(attribute_id=3, name="2.4", value="2.4", slug="2.4"),
            attrvalue(attribute_id=3, name="2.5", value="2.5", slug="2.5"),
            attrvalue(attribute_id=3, name="2.6", value="2.6", slug="2.6"),
            attrvalue(attribute_id=3, name="2.7", value="2.7", slug="2.7"),
            attrvalue(attribute_id=3, name="2.8", value="2.8", slug="2.8"),
            attrvalue(attribute_id=3, name="2.9", value="2.9", slug="2.9"),
            attrvalue(attribute_id=5, name="Gents", value="gents", slug="gents"),
            attrvalue(attribute_id=5, name="Ladies", value="Ladies", slug="ladies"),
            attrvalue(attribute_id=5, name="Boys", value="boys", slug="boys"),
            attrvalue(attribute_id=5, name="Baby", value="baby", slug="baby"),
            attrvalue(attribute_id=4, name="Long", value="Long", slug="long"),
            attrvalue(attribute_id=4, name="short", value="short", slug="short"),
            attrvalue(attribute_id=6, name="0.5 gm", value="0.5", slug="0.5g"),
            attrvalue(attribute_id=6, name="1 gm", value="1 gm", slug="1g"),
            attrvalue(attribute_id=6, name="1.5 gm", value="1.5 gm", slug="1.5g"),
            attrvalue(attribute_id=6, name="2 gm", value="2g", slug="2g"),
            attrvalue(attribute_id=6, name="3 gm", value="3g", slug="3g"),
            attrvalue(attribute_id=6, name="4 gm", value="4g", slug="4g"),
            attrvalue(attribute_id=6, name="6 gm", value="6g", slug="6g"),
            attrvalue(attribute_id=6, name="8 gm", value="8g", slug="8g"),
            attrvalue(attribute_id=6, name="10 gm", value="10g", slug="10g"),
            attrvalue(attribute_id=6, name="12 gm", value="12g", slug="12g"),
            attrvalue(attribute_id=6, name="16 gm", value="16g", slug="16g"),
            attrvalue(attribute_id=6, name="20 gm", value="20g", slug="20g"),
            attrvalue(attribute_id=6, name="24 gm", value="24g", slug="24g"),
            attrvalue(attribute_id=6, name="32 gm", value="32g", slug="32g"),
            attrvalue(attribute_id=6, name="40 gm", value="40g", slug="40g"),
        ]
    )


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(insertData),
        migrations.RunPython(rebuild_category, noop_reverse),
    ]
