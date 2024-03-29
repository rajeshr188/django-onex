# Generated by Django 4.2.3 on 2023-07-23 11:17

from django.db import migrations
from django.db.migrations.operations.base import Operation


class CreateView(Operation):
    reversible = True

    def __init__(self, name, sql):
        self.name = name
        self.sql = sql

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(f"CREATE VIEW {self.name} AS {self.sql}")

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(f"DROP VIEW IF EXISTS {self.name};")

    def describe(self):
        return "Creates VIEW %s" % self.name

    @property
    def migration_name_fragment(self):
        return "create_view_%s" % self.name


class Migration(migrations.Migration):
    dependencies = [
        ("dea", "0002_initial_fixture"),
    ]

    ledger_balance_sql_v1 = """
        WITH ls AS (
        SELECT DISTINCT ON (dea_ledgerstatement.ledgerno_id) dea_ledgerstatement.id,
            dea_ledgerstatement.created,
            dea_ledgerstatement."ClosingBalance",
            dea_ledgerstatement.ledgerno_id
           FROM dea_ledgerstatement
          ORDER BY dea_ledgerstatement.ledgerno_id, dea_ledgerstatement.created DESC
        )
        SELECT dea_ledger.id AS ledgerno_id,
            dea_ledger.name,
            at."AccountType",
            ls.created,
            ls."ClosingBalance",
            ARRAY( SELECT ROW(sum(dea_ledgertransaction.amount)::numeric(14,0), dea_ledgertransaction.amount_currency)::money_value AS "row"
                FROM dea_ledgertransaction
                WHERE dea_ledgertransaction.ledgerno_id = dea_ledger.id 
                AND (ls.created IS NULL OR dea_ledgertransaction.created >= ls.created)
                GROUP BY dea_ledgertransaction.amount_currency) AS cr,
            ARRAY( SELECT ROW(sum(dea_ledgertransaction.amount)::numeric(14,0), 
            dea_ledgertransaction.amount_currency)::money_value AS "row"
                FROM dea_ledgertransaction
                WHERE dea_ledgertransaction.ledgerno_dr_id = dea_ledger.id AND (ls.created IS NULL OR dea_ledgertransaction.created >= ls.created)
                GROUP BY dea_ledgertransaction.amount_currency) AS dr
        FROM dea_ledger
        LEFT JOIN ls ON dea_ledger.id = ls.ledgerno_id
        JOIN dea_accounttype at ON at.id = dea_ledger."AccountType_id";        
            """

    ledger_balance_sql = """
         WITH ls AS (
         SELECT DISTINCT ON (dea_ledgerstatement.ledgerno_id) dea_ledgerstatement.id,
            dea_ledgerstatement.created,
            dea_ledgerstatement."ClosingBalance",
            dea_ledgerstatement.ledgerno_id,
            dl.id,
            dl.name,
            dl.lft,
            dl.rght,
            dl.tree_id,
            dl.level,
            dl."AccountType_id",
            dl.parent_id
           FROM dea_ledgerstatement
             JOIN dea_ledger dl ON dl.id = dea_ledgerstatement.ledgerno_id
          ORDER BY dea_ledgerstatement.ledgerno_id, dea_ledgerstatement.created DESC
        )
        SELECT ls.ledgerno_id,
            ls.created,
            ls.name,
            at."AccountType",
            ls."ClosingBalance",
            ARRAY( SELECT ROW(sum(dea_ledgertransaction.amount)::numeric(14,0), dea_ledgertransaction.amount_currency)::money_value AS "row"
                FROM dea_ledgertransaction
                WHERE dea_ledgertransaction.ledgerno_id = ls.ledgerno_id AND dea_ledgertransaction.created >= ls.created
                GROUP BY dea_ledgertransaction.amount_currency) AS cr,
            ARRAY( SELECT ROW(sum(dea_ledgertransaction.amount)::numeric(14,0), dea_ledgertransaction.amount_currency)::money_value AS "row"
                FROM dea_ledgertransaction
                WHERE dea_ledgertransaction.ledgerno_dr_id = ls.ledgerno_id AND dea_ledgertransaction.created >= ls.created
                GROUP BY dea_ledgertransaction.amount_currency) AS dr
        FROM ls ls(id, created, "ClosingBalance", ledgerno_id, id_1, name, lft, rght, tree_id, level, "AccountType_id", parent_id)
            JOIN dea_accounttype at ON at.id = ls."AccountType_id";
    """
    ledger_balance_with_lt_and_at_sql = """
        WITH ls AS (
            SELECT DISTINCT ON (dea_ledgerstatement.ledgerno_id) dea_ledgerstatement.id,
                dea_ledgerstatement.created,
                dea_ledgerstatement."ClosingBalance",
                dea_ledgerstatement.ledgerno_id,
                dl.id,
                dl.name,
                dl.lft,
                dl.rght,
                dl.tree_id,
                dl.level,
                dl."AccountType_id",
                dl.parent_id
            FROM dea_ledgerstatement
                JOIN dea_ledger dl ON dl.id = dea_ledgerstatement.ledgerno_id
            ORDER BY dea_ledgerstatement.ledgerno_id, dea_ledgerstatement.created DESC
            )
        SELECT ls.ledgerno_id,
            ls.created,
            ls.name,
            at."AccountType",
            ls."ClosingBalance",
            ARRAY( SELECT ROW(sum(dea_ledgertransaction.amount)::numeric(14,0), dea_ledgertransaction.amount_currency)::money_value AS "row"
                FROM dea_ledgertransaction
                WHERE dea_ledgertransaction.ledgerno_id = ls.ledgerno_id AND dea_ledgertransaction.created >= ls.created
                GROUP BY dea_ledgertransaction.amount_currency) AS ll_cr,
            ARRAY( SELECT ROW(sum(dea_ledgertransaction.amount)::numeric(14,0), dea_ledgertransaction.amount_currency)::money_value AS "row"
                FROM dea_ledgertransaction
                WHERE dea_ledgertransaction.ledgerno_dr_id = ls.ledgerno_id AND dea_ledgertransaction.created >= ls.created
                GROUP BY dea_ledgertransaction.amount_currency) AS ll_dr,
            ARRAY( SELECT ROW(sum(dea_accounttransaction.amount)::numeric(14,0), dea_accounttransaction.amount_currency)::money_value AS "row"
                FROM dea_accounttransaction
                WHERE dea_accounttransaction.ledgerno_id = ls.ledgerno_id AND dea_accounttransaction."XactTypeCode_id"::text = 'Dr'::text 
                GROUP BY dea_accounttransaction.amount_currency) AS la_cr,
            ARRAY( SELECT ROW(sum(dea_accounttransaction.amount)::numeric(14,0), dea_accounttransaction.amount_currency)::money_value AS "row"
                FROM dea_accounttransaction
                WHERE dea_accounttransaction.ledgerno_id = ls.ledgerno_id AND dea_accounttransaction."XactTypeCode_id"::text = 'Cr'::text 
                GROUP BY dea_accounttransaction.amount_currency) AS la_dr
        FROM ls ls(id, created, "ClosingBalance", ledgerno_id, id_1, name, lft, rght, tree_id, level, "AccountType_id", parent_id)
            JOIN dea_accounttype at ON at.id = ls."AccountType_id";
    """
    account_balance_sql_v1 = """
        WITH acc_st AS (
            SELECT DISTINCT ON (dea_accountstatement."AccountNo_id") dea_accountstatement.id,
                dea_accountstatement.created,
                dea_accountstatement."ClosingBalance",
                dea_accountstatement."TotalCredit",
                dea_accountstatement."TotalDebit",
                dea_accountstatement."AccountNo_id"
            FROM dea_accountstatement
            ORDER BY dea_accountstatement."AccountNo_id", dea_accountstatement.created DESC
            )
        SELECT dea_account.id AS "AccountNo_id",
            ate.description,
            et.name AS entity,
            ct.name AS contact,
            acc_st.created,
            acc_st."ClosingBalance",
            acc_st."TotalCredit",
            acc_st."TotalDebit",
            ARRAY( SELECT ROW(sum(dea_accounttransaction.amount)::numeric(14,0), dea_accounttransaction.amount_currency)::money_value AS "row"
                FROM dea_accounttransaction
                WHERE dea_accounttransaction."Account_id" = dea_account.id 
                AND dea_accounttransaction."XactTypeCode_id"::text = 'Dr'::text 
                AND ((acc_st.created isnull) or dea_accounttransaction.created >= acc_st.created)
                GROUP BY dea_accounttransaction.amount_currency) AS cr,
            ARRAY( SELECT ROW(sum(dea_accounttransaction.amount)::numeric(14,0), dea_accounttransaction.amount_currency)::money_value AS "row"
                FROM dea_accounttransaction
                WHERE dea_accounttransaction."Account_id" = dea_account.id 
                AND dea_accounttransaction."XactTypeCode_id"::text = 'Cr'::text 
                AND ((acc_st.created isnull) or dea_accounttransaction.created >= acc_st.created)
                GROUP BY dea_accounttransaction.amount_currency) AS dr
        FROM dea_account
            LEFT JOIN acc_st ON dea_account.id = acc_st."AccountNo_id"
            JOIN dea_accounttype_ext ate ON ate.id = dea_account."AccountType_Ext_id"
            JOIN contact_customer ct ON ct.id = dea_account.contact_id
            JOIN dea_entitytype et ON et.id = dea_account.entity_id;
    """
    account_balance_sql = """
    
        WITH astmt AS
        (
         SELECT DISTINCT ON (dea_accountstatement."AccountNo_id") et.name AS entity,
            acte.description AS acc_type,
            cu.name AS acc_name,
            dea_accountstatement.id,
            dea_accountstatement.created,
            dea_accountstatement."ClosingBalance",
            dea_accountstatement."TotalCredit",
            dea_accountstatement."TotalDebit",
            dea_accountstatement."AccountNo_id"
           FROM dea_accountstatement
             JOIN dea_account acc ON acc.id = dea_accountstatement."AccountNo_id"
             JOIN dea_accounttype_ext acte ON acte.id = acc."AccountType_Ext_id"
             JOIN dea_entitytype et ON et.id = acc.entity_id
             JOIN contact_customer cu ON cu.id = acc.contact_id
          ORDER BY dea_accountstatement."AccountNo_id", dea_accountstatement.created DESC
        )
        SELECT astmt.acc_name,
            astmt.entity,
            astmt.acc_type,
            astmt.id,
            astmt.created,
            astmt."ClosingBalance",
            astmt."TotalCredit",
            astmt."TotalDebit",
            astmt."AccountNo_id",
            ARRAY( SELECT ROW(sum(dea_accounttransaction.amount)::numeric(14,0), dea_accounttransaction.amount_currency)::money_value AS "row"
                FROM dea_accounttransaction
                WHERE dea_accounttransaction."Account_id" = astmt."AccountNo_id" 
                AND dea_accounttransaction."XactTypeCode_id"::text = 'Dr'::text 
                AND dea_accounttransaction.created >= astmt.created
                GROUP BY dea_accounttransaction.amount_currency) AS cr,
            ARRAY( SELECT ROW(sum(dea_accounttransaction.amount)::numeric(14,0), dea_accounttransaction.amount_currency)::money_value AS "row"
                FROM dea_accounttransaction
                WHERE dea_accounttransaction."Account_id" = astmt."AccountNo_id" 
                AND dea_accounttransaction."XactTypeCode_id"::text = 'Cr'::text 
                AND dea_accounttransaction.created >= astmt.created
                GROUP BY dea_accounttransaction.amount_currency) AS dr
        FROM astmt;
    """
    operations = [
        CreateView("ledger_balance", ledger_balance_sql_v1),
        CreateView("account_balance", account_balance_sql_v1),
    ]
