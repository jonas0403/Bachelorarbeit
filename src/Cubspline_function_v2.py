# Author: Marco Wiens
# Version:09.04.2024
# Cubspline function
# funcions for spline calculation

import debug_log

def spline(x, y, N, yp1, ypn, y2):
    
    """ 
    Part one of Method 1
    Given arrays x(1:n) and y(1:n) containing a tabulated function, i.e., y i = f(xi), with x1<x2< ::: < xN , and given values yp1
    and ypn for the first derivative of the interpolating function at points 1 and n, respectively, this routine returns an array y2(1:n)
    of length n which contains the second derivatives of the interpolating function at the tabulated points xi. If yp1 and/or ypn are equal
    to 1 * 10^30 or larger, the routine is signaled to set the corresponding boundary condition for a natural spline, with zero second derivative on that boundary.
    Parameter: NMAX is the largest anticipated value of n.
    """

    Nmax = 500
    U = [0] * Nmax

    # The lower boundary condition is set either to be natural
    if yp1 > 9.9E+29:
        y2[0] = 0
        U[0] = 0
    else:
        # or else to have a specified first derivative.
        y2[0] = -0.5
        U[0] = (3 / (x[1] - x[0])) * ((y[1] - y[0]) / (x[1] - x[0]) - yp1)


    #This is the decomposition loop of the tridiagonal algorithm. y2 and u are used for temporary storage of the decomposed factors.
    for i in range(1, N - 1):
        sig = (x[i] - x[i - 1]) / (x[i + 1] - x[i - 1])
        p = sig * y2[i - 1] + 2
        y2[i] = (sig - 1) / p
        U[i] = (6 * ((y[i + 1] - y[i]) / (x[i + 1] - x[i]) - (y[i] - y[i - 1]) /
                     (x[i] - x[i - 1])) / (x[i + 1] - x[i - 1]) - sig * U[i - 1]) / p

    # The upper boundary condition is set either to be natural
    if ypn > 9.9E+29:
        qn = 0
        un = 0
    else:
        # or else to have a specified first derivative.
        qn = 0.5
        un = (3 / (x[N - 1] - x[N - 2])) * (ypn - (y[N - 1] - y[N - 2]) /
                                             (x[N - 1] - x[N - 2]))

    y2[N - 1] = (un - qn * U[N - 2]) / (qn * y2[N - 2] + 1)

    # This is the backsubstitution loop of the tridiagonal algorithm.
    for k in range(N - 2, -1, -1):
        y2[k] = y2[k] * y2[k + 1] + U[k]

def splint(xa, ya, y2a, N, x):
    
    """
    Part two of Method 1
    Given the arrays xa(1:n) and ya(1:n) of length n, which tabulate a function (with the xai 's in order), and given the array y2a(1:n), which is the
    output from spline above, and given a value of x, this routine returns a cubic-spline interpolated value y.
    """

    # We will find the right place in the table by means of bisection.
    klo = 0
    khi = N - 1

    while (khi - klo > 1):
        k = (khi + klo) // 2
        if (xa[k] > x):
            khi = k
        else:
            klo = k

    # klo and khi now bracket the input value of x.
    h = xa[khi] - xa[klo]
    if (h == 0):
        spline_err = "bad xa input in splint"
        print(spline_err)
        debug_log.debug(spline_err, context="splint")

    # Cubic spline polynomial is now evaluated.
    A = (xa[khi] - x) / h
    B = (x - xa[klo]) / h
    y = A * ya[klo] + B * ya[khi] + ((A ** 3 - A) * y2a[klo] + (B ** 3 - B) * y2a[khi]) * (h ** 2) / 6

    return y

def dxx(x1, x0):
    # Calc Xi - Xi-1 to prevent div by zero
    dxx = x1 - x0
    if dxx == 0:
        dxx = 1e30
    return dxx

def spline_x3(x, xx, yy):
    # Function returns y value for a corresponding x value, based on cubic spline.
    # Will never oscillates or overshoot. No need to solve matrix.
    # Also calculate constants for cubic in case needed (for integration).

    # Find LineNumber or segment. Linear extrapolate if outside range.
    num = 0
    if x < xx[0] or x > xx[-1]:
        # X outside range. Linear interpolate
        # Below min or max?
        if x < xx[0]:
            num = 1
        else:
            num = len(xx) - 1
        b = (yy[num] - yy[num - 1]) / dxx(xx[num], xx[num - 1])
        a = yy[num] - b * xx[num]
        return a + b * x
    else:
        # X in range. Get line.
        for i in range(1, len(xx)):
            if x <= xx[i]:
                num = i
                break

    # Calc first derivative (slope) for intermediate points
    gxx = [0, 0]  # Two points around line
    for j in range(2):
        i = num - 1 + j
        if i == 0 or i == len(xx) - 1:
            # Set very large slope at ends
            gxx[j] = 10 ** 30
        elif (yy[i + 1] - yy[i] == 0) or (yy[i] - yy[i - 1] == 0):
            # Only check for 0 dy. dx assumed NEVER equals 0 !
            gxx[j] = 0
        elif ((xx[i + 1] - xx[i]) / (yy[i + 1] - yy[i]) + (xx[i] - xx[i - 1]) /
              (yy[i] - yy[i - 1])) == 0:
            # Pos PLUS neg slope is 0. Prevent div by zero.
            gxx[j] = 0
        elif (yy[i + 1] - yy[i]) * (yy[i] - yy[i - 1]) < 0:
            # Pos AND neg slope, assume slope = 0 to prevent overshoot
            gxx[j] = 0
        else:
            # Calculate an average slope for point based on connecting lines
            gxx[j] = 2 / ((xx[i + 1] - xx[i]) / (yy[i + 1] - yy[i]) +
                          (xx[i] - xx[i - 1]) / (yy[i] - yy[i - 1]))

    # Reset first derivative (slope) at first and last point
    if num == 1:
        # First point has 0 2nd derivative
        gxx[0] = 3 / 2 * (yy[num] - yy[num - 1]) / dxx(xx[num], xx[num - 1]) - gxx[1] / 2
    if num == len(xx) - 1:
        # Last point has 0 2nd derivative
        gxx[1] = 3 / 2 * (yy[num] - yy[num - 1]) / dxx(xx[num], xx[num - 1]) - gxx[0] / 2

    # Calc second derivative at points
    ggxx = [-2 * (gxx[1] + 2 * gxx[0]) / dxx(xx[num], xx[num - 1]) + 6 * (yy[num] - yy[num - 1]) / dxx(xx[num], xx[num - 1]) ** 2,
            2 * (2 * gxx[1] + gxx[0]) / dxx(xx[num], xx[num - 1]) - 6 * (yy[num] - yy[num - 1]) / dxx(xx[num], xx[num - 1]) ** 2]

    # Calc constants for cubic
    D = 1 / 6 * (ggxx[1] - ggxx[0]) / dxx(xx[num], xx[num - 1])
    C = 1 / 2 * (xx[num] * ggxx[0] - xx[num - 1] * ggxx[1]) / dxx(xx[num], xx[num - 1])
    B = (yy[num] - yy[num - 1] - C * (xx[num] ** 2 - xx[num - 1] ** 2) -  D * (xx[num] ** 3 - xx[num - 1] ** 3)) / dxx(xx[num], xx[num - 1])
    A = yy[num - 1] - B * xx[num - 1] - C * xx[num - 1] ** 2 - D * xx[num - 1] ** 3

    # Return function
    return A + B * x + C * x ** 2 + D * x ** 3

def cubspline(Method, xi, xx, yy):
    # valid input for parameter "Method": 1 = cubic spline / 3 = own spline

    # Numerical Recipes are 1 based
    if Method == 1:
        j = 0
    else:
        # Others are 0 based
        j = -1

    x = []
    y = []

    for i in range(len(xx)):
        if yy[i] != "":
            j += 1
            x.append(float(xx[i]))
            y.append(float(yy[i]))

    if Method == 1:
        # NR cubic spline
        # Get y2
        y2 = [0] * len(x)
        spline(x, y, len(x), 1e30, 1e30, y2)
        # Get y
        yi = splint(x, y, y2, len(x), xi)
    elif Method == 3:
        # Own cubic spline
        yi = spline_x3(xi, x, y)

    return yi
