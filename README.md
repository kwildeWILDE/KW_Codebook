# KW_Codebook
Kendall's code book for getting practice for working on live datasets from the FC.

The 2024 50 m KDE example compares its manual bivariate Gaussian KDE with
`scipy.stats.gaussian_kde` at each valid wind-speed/temperature pair. Both use
Silverman's rule and the full sample covariance matrix. The optional,
commented-out CSV export retains the manual `KDE` column and adds SciPy
densities and absolute differences. Rows with missing or non-finite wind speed
or temperature are excluded from the KDE, plots, and optional CSV.

The example also saves `kernel_orientation.gif`, showing the individual
Gaussian kernel centered on each of the first 25 valid points (or all points
if fewer than 25). The kernels share the same covariance matrix H, so their
shape and orientation do not change. The optional CSV records H's three
unique components and the dimensionless Silverman bandwidth factor; the
factor is not a replacement for the full matrix.
