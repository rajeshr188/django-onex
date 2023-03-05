from reportlab.lib.pagesizes import letter, landscape, A4, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Flowable,
    Frame,
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    Image,
    TableStyle,
    ListFlowable,
    ListItem,
    PageBreak,
)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import io
from num2words import num2words
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER, TA_RIGHT
from girvi.models import Loan
from contact.models import Customer

from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm, inch


PAGESIZE = (140 * mm, 216 * mm)
BASE_MARGIN = 5 * mm


class PdfCreator:
    def add_page_number(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 10)
        page_number_text = "%d" % (doc.page)
        canvas.drawCentredString(0.75 * inch, 0.75 * inch, page_number_text)
        canvas.restoreState()

    def get_body_style(self):
        sample_style_sheet = getSampleStyleSheet()
        body_style = sample_style_sheet["BodyText"]
        body_style.fontSize = 18
        return body_style

    def build_pdf(self):
        pdf_buffer = BytesIO()
        my_doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=PAGESIZE,
            topMargin=BASE_MARGIN,
            leftMargin=BASE_MARGIN,
            rightMargin=BASE_MARGIN,
            bottomMargin=BASE_MARGIN,
        )
        body_style = self.get_body_style()
        flowables = [
            Paragraph("First paragraph", body_style),
            Paragraph("Second paragraph", body_style),
        ]
        my_doc.build(
            flowables,
            onFirstPage=self.add_page_number,
            onLaterPages=self.add_page_number,
        )
        pdf_value = pdf_buffer.getvalue()
        pdf_buffer.close()
        return pdf_value


class CentreLine(Flowable):
    """
    Draws a dotted line in the centre of the page vertically to tear along
    """

    def __init__(self):
        Flowable.__init__(self)

    def draw(self):
        # Set the line width and style
        self.canv.setLineWidth(0.5)
        self.canv.setDash(1, 3)  # 1pt on, 3pt off

        # Calculate the center of the page
        center_x = landscape(A4)[0] / 2
        center_y = landscape(A4)[1] / 2

        # Draw the dotted line from top to bottom at the center of the page
        self.canv.line(center_x, landscape(A4)[1], center_x, 0)


class BoxyLine(Flowable):
    """
    Draw a box + line + text

    -----------------------------------------
    | foobar |
    ---------

    """

    def __init__(self, x=0, y=-15, width=40, height=15, text=""):
        Flowable.__init__(self)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def draw(self):
        """
        Draw the shape, text, etc
        """
        # self.canv.rect(self.x, self.y, self.width, self.height)
        self.canv.line(self.x, 0, 350, 0)
        self.canv.drawString(self.x + 5, self.y + 3, self.text)


def get_loan_pdf(loan):
    pdfmetrics.registerFont(
        TTFont("NotoSansTamil-Regular", "static/fonts/NotoSansTamil-Regular.ttf")
    )
    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()
    my_canvas = Canvas(buffer, pagesize=landscape(A4))
    w, h = my_canvas._pagesize
    spacer = Spacer(0, 0.25 * inch)

    # Define styles for the paragraphs
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    heading = styles["Heading1"]
    normal.alignment = TA_JUSTIFY

    # Define the text for the paragraphs

    shop = """<font color=blue size=14>J Champalal</font> <br />
                <font size = 10 >Pawn Brokers</font>
                no:8, Lathid sahib street,<br />
                R.N Palayam,Vellore<br/>
                Phone:2416-2232536"""
    customer = f"""
                    {loan.customer.name} {loan.customer.relatedas} {loan.customer.relatedto}<br/>
                    {loan.customer.Address}<br />
                    {loan.customer.area}
                    vellore,632001<br />
                    ph:{loan.customer.contactno}
                    """

    # Create the Paragraph objects
    logo = Image("static/images/falconx.png", 50, 50)
    # print(loan.customer)
    # customer_img = Image(loan.customer.pic.url,50,50)

    simple_tblstyle = TableStyle(
        [
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
        ]
    )

    header = Table(
        [
            [
                Paragraph("Sec Rules 8"),
                Paragraph(
                    "Pawn Ticket <font size = 14 name='NotoSansTamil-Regular'>அடகு சீட்டு   </font>"
                ),
                Paragraph("PBL NO:1515/2017"),
            ]
        ]
    )
    # table1.setStyle(simple_tblstyle)
    shop = Table(
        [
            [logo, Paragraph(shop, normal)],
        ]
    )
    loanid_date = Table(
        [
            [
                Paragraph(f"LoanID : {loan.loanid}"),
                Paragraph(f"Date: {loan.created.date()}"),
            ]
        ]
    )
    loanid_date.setStyle(simple_tblstyle)
    loanitems = Table(
        [
            [
                ListFlowable(
                    [
                        # ListItem(Paragraph('Paragraph #2', normal),
                        #         bulletColor="blue",),
                        Paragraph(f"{loan.itemdesc}", normal),
                    ]
                )
            ]
        ]
    )
    loanitems.setStyle(simple_tblstyle)
    loanitem_details = Table(
        [
            [
                Paragraph(f"Gross Wt: {loan.itemweight} gms"),
                Paragraph("Nett Wt: 100.00"),
                Paragraph(f"Value: {loan.itemvalue}"),
            ]
        ]
    )
    loanitem_details.setStyle(simple_tblstyle)
    amount_tbl = Table(
        [
            [
                Paragraph(f"Loan Amount: {loan.loanamount}"),
                Paragraph(
                    f"Loan Amount In Words<br/>{num2words(loan.loanamount, lang='en_IN')}"
                ),
            ],
        ]
    )
    amount_tbl.setStyle(simple_tblstyle)
    terms = Table(
        [
            [
                ListFlowable(
                    [
                        Paragraph(
                            "Time agreed for redemption of articles is 3 months.",
                            normal,
                        ),
                        Paragraph("Above mentioned articles are my own"),
                        # ListItem(Paragraph('Paragraph #2', normal),
                        #          bulletColor="blue",),
                    ]
                )
            ]
        ]
    )
    terms.setStyle(simple_tblstyle)
    signature = Table(
        [
            ["", ""],
            [
                Paragraph(
                    "<font size=8 >Signature/Thumb Impression of the pawner</font>"
                ),
                Paragraph(
                    "<font size=8 >Signature of the Pawn broker/his Agent</font>"
                ),
            ],
        ]
    )
    signature.setStyle(simple_tblstyle)

    flowables = [header]
    # flowables.append(CentreLine())
    flowables.append(shop)
    flowables.append(spacer)
    flowables.append(loanid_date)
    flowables.append(BoxyLine(text="Customer"))
    flowables.append(spacer)
    flowables.append(
        Table(
            [
                [logo, Paragraph(customer, normal)],
            ]
        )
    )
    flowables.append(BoxyLine(text="Following article/s are pawned with me:"))
    flowables.append(spacer)
    flowables.append(loanitems)
    flowables.append(loanitem_details)
    flowables.append(amount_tbl)

    flowables.append(BoxyLine(text="Terms & Conditions"))
    flowables.append(spacer)
    flowables.append(terms)
    flowables.append(Paragraph("  My monthly income is above Rs:"))
    flowables.append(spacer)
    flowables.append(signature)

    right_flowables = [*flowables]
    right_flowables.append(spacer)

    right_flowables.append(
        Table(
            [
                [loan.loanid, loan.created.date()],
                [loan.loanamount, loan.itemweight],
                [loan.customer.name, loan.itemdesc],
            ]
        )
    )

    # right_flowables.append(Paragraph('ipsum lorem', normal))

    left_frame = Frame(
        10 * mm, 10 * mm, width=(w - 30 * mm) / 2, height=h - 20 * mm, showBoundary=1
    )
    right_frame = Frame(
        (w + 10 * mm) / 2,
        10 * mm,
        width=(w - 30 * mm) / 2,
        height=h - 20 * mm,
        showBoundary=1,
    )

    left_frame.addFromList(flowables, my_canvas)
    right_frame.addFromList(right_flowables, my_canvas)

    # Set the line width and style
    my_canvas.setLineWidth(0.5)
    my_canvas.setDash(1, 3)  # 1pt on, 3pt off

    # Calculate the center of the page
    center_x = landscape(A4)[0] / 2
    center_y = landscape(A4)[1] / 2

    # Draw the dotted line from top to bottom at the center of the page
    my_canvas.line(center_x, landscape(A4)[1], center_x, 0)
    my_canvas.line(w / 2, 100, w, 100)

    my_canvas.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def get_notice_pdf(selection=None):
    # # get all loans with selected ids
    # selected_loans = Loan.unreleased.filter(id__in=selection).order_by("customer")
    selected_loans = selection
    # get a list of unique customers for the selected loans
    customers = Customer.objects.filter(loan__in=selected_loans).distinct()

    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()
    # Create the PDF canvas
    # pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
    doc = SimpleDocTemplate(buffer)
    # Define styles for the paragraphs
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Normal_CENTER",
            parent=styles["Normal"],
            fontName="Helvetica",
            wordWrap="LTR",
            alignment=TA_CENTER,
            fontSize=12,
            leading=13,
            textColor=colors.black,
            borderPadding=0,
            leftIndent=0,
            rightIndent=0,
            spaceAfter=0,
            spaceBefore=0,
            splitLongWords=True,
            spaceShrinkage=0.05,
        )
    )
    top = styles["Normal_CENTER"]
    normal = styles["Normal"]
    title = styles["Title"]
    heading = styles["Heading1"]
    story = []
    spacer = Spacer(0, 0.25 * inch)
    # Loop through each customer
    for customer in customers:
        # Calculate the total loan amount for the customer
        # total_loan_amount = loans.aggregate(Sum('loanamount'))['loanamount__sum'] or 0
        story.append(spacer)
        story.append(Paragraph("TAMILNADU PAWNBROKERS ACT, 1943", top))
        story.append(spacer)
        story.append(Paragraph("NOTICE TO REDEEM PLEDGE", heading))
        story.append(spacer)
        story.append(
            Paragraph(
                f"""
            To,<br/>
            {customer.name} {customer.relatedas} {customer.relatedto}<br/>
            {customer.Address}<br/>
            {customer.area}<br/>
            {customer.contactno}

        """
            )
        )
        story.append(spacer)
        story.append(
            Paragraph(
                """
        Notice is hereby given that the Pledge of the following article(s) is now <br/>
        at the Pawn Broker named below, and that unless the same is redeemed within<br/>
        30 days from the date hereof, it will be sold by public auction at the Pawn<br/>
        Broker's place of business, without further notice to the Pledger or his agent.<br/>
        """
            )
        )
        story.append(spacer)
        story.append(
            Paragraph(
                f"""
        Name of Pawn Broker:J Champalal Pawn Brokers

        """
            )
        )
        story.append(Paragraph("Description of Articles Pledged:"))

        # Write the customer details to the PDF
        # Get all loans for the current customer
        loans = selected_loans.filter(customer=customer)
        width = 400
        height = 100
        x = 100
        y = 300
        f = Table(
            [
                [item.loanid, item.itemweight, item.created, item.itemdesc]
                for item in loans
            ]
        )
        simple_tblstyle = TableStyle(
            [
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ]
        )
        f.setStyle(simple_tblstyle)
        story.append(spacer)
        story.append(f)
        story.append(PageBreak())

    # Save the PDF and return the response
    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
