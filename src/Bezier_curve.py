# Author: Marco Wiens
# Version: 12.12.2024
# Bezier curve
# function for calculation of Bézier curve


import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Slider
import debug_log

def bezier(Points, t, yy):
    yb = 9999
    if Points == 4:
        # Bezier with 4 points
        yb = yy[0] * (1 - t) ** 3 + 3 * yy[1] * t * (1 - t) ** 2 + 3 * yy[2] * t ** 2 * (1 - t) + yy[3] * t ** 3
    elif Points == 5:
        # Bezier with 5 points
        yb = yy[0] * (1 - t) ** 4 + 4 * yy[1] * t * (1 - t) ** 3 + 6 * yy[2] * t ** 2 * (1 - t) ** 2 + \
             4 * yy[3] * t ** 3 * (1 - t) + yy[4] * t ** 5
    elif Points == 6:
        # Bezier with 6 points
        yb = yy[0] * (1 - t) ** 5 + 5 * yy[1] * t * (1 - t) ** 4 + 20 * yy[2] * t ** 2 * (1 - t) ** 3 + \
             20 * yy[3] * t ** 3 * (1 - t) ** 2 + 5 * yy[4] * t ** 4 * (1 - t) + yy[5] * t ** 5
    return yb

def adjustBezierCurve(BezierPoints):

    d_lB = BezierPoints
    mB = [0.0, 0.3, 0.7, 1.0] 
    t = np.arange(0, 1.01, 0.01)

    x = bezier(4, t, mB)
    y = bezier(4, t, d_lB)

    # Create the plot
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.5)  # Leave more space for the sliders

    # Plot the points
    points, = plt.plot(mB, d_lB, 'o-', label="Points")
    curve, = plt.plot(x,y)
    plt.title("Béziercurve")
    plt.xlabel("m")
    plt.ylabel("d/l")


    # Set axis limits
    ax.set_xlim(0, 1)

    d_l_min = 0.0
    d_l_max = 3.0

    ax.set_ylim(d_l_min, d_l_max)

    # Add sliders for each point
    sliders = []  # Store slider objects
    slider_axes = []  # Store axes for sliders

    for i in range(4):  # Create one slider for each point
        ax_slider = plt.axes([0.2, 0.25 - i * 0.05, 0.65, 0.03], facecolor='lightgoldenrodyellow')
        slider = Slider(ax_slider, f'Point {i + 1}', d_l_min, d_l_max, valinit=d_lB[i])
        sliders.append(slider)
        slider_axes.append(ax_slider)

    # Define update function for sliders
    def update(val):
        for i, slider in enumerate(sliders):
            d_lB[i] = slider.val  # Update y-coordinate for each point
        
        y = bezier(4, t, d_lB)
        curve.set_ydata(y)
        points.set_ydata(d_lB)  # Update the plot
        fig.canvas.draw_idle()

    # Connect sliders to the update function
    for slider in sliders:
        slider.on_changed(update)

    # Show the interactive plot
    plt.show()
    for i in range(len(d_lB)):
        d_lB[i] = round(d_lB[i], 2)

    bezier_msg = f"New Bezier Point: {d_lB}"
    print(bezier_msg)
    debug_log.debug(bezier_msg, context="bezier")
    return BezierPoints