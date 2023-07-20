from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def draw_reference_grid():
    c = canvas.Canvas("reference_grid.pdf", pagesize=letter)

    # Paper size
    page_width, page_height = letter

    # Grid spacing
    grid_spacing = 50  # Adjust this value based on your preference

    # Calculate the number of lines
    num_horizontal_lines = int(page_height / grid_spacing)
    num_vertical_lines = int(page_width / grid_spacing)

    # Draw horizontal lines
    for i in range(num_horizontal_lines):
        y = i * grid_spacing
        c.line(0, y, page_width, y)

    # Draw vertical lines
    for i in range(num_vertical_lines):
        x = i * grid_spacing
        c.line(x, 0, x, page_height)

    # Add labels (optional)
    # You can customize the labels as per your requirements
    for i in range(num_horizontal_lines):
        y = i * grid_spacing
        c.drawString(5, y, f"y={y}")

    for i in range(num_vertical_lines):
        x = i * grid_spacing
        c.drawString(x, 5, f"x={x}")

    c.save()


# Call the function to draw the reference grid
draw_reference_grid()
