import openpyxl

from contact.models import Customer
from girvi.models import Loan, LoanItem

# Load the Excel file
workbook = openpyxl.load_workbook("table.xlsx")
sheet = workbook.active  # Assuming the data is in the active sheet

data_to_update = {}  # Create a dictionary to store data (key: ID, value: Field Value)

# Iterate through rows and store data in the dictionary
for row in sheet.iter_rows(min_row=2, values_only=True):  # Skip header row
    # id_value, item,wt,amount,interest = row
    data_to_update[row[0]] = row


for id_value, field_value in data_to_update.items():
    try:
        obj = LoanItem.objects.get(
            loan__loanid=id_value
        )  # Assuming 'id' is the primary key
        print(f"id:{id_value} fields:{field_value}")
        obj.weight = field_value[
            2
        ]  # Replace 'deleted_field' with your actual field name

        obj.save()
        print(f"obj:{obj.loan} wt:{obj.weight}")
    except LoanItem.MultipleObjectsReturned:
        pass
    except LoanItem.DoesNotExist:
        print(f"Loan item for {id_value} doesnot exist so creating")
        loan = Loan.objects.get(loanid=id_value)
        if loan.itemtype == "Gold":
            intrate = 2
        else:
            intrate = 4
        obj = LoanItem.objects.create(
            loan=loan,
            loanamount=loan.loanamount,
            weight=field_value[2],
            itemtype=loan.itemtype,
            itemdesc=loan.itemdesc,
            interestrate=intrate,
        )
        print(f"obj:{obj.loan} wt:{obj.weight}")

        # Handle cases where the ID doesn't exist in the database

# Close the workbook

workbook.close()
