# Outlier Highlighting Implementation Guide

## Overview
This document describes how the modified KDE plots identify and highlight outlier points from May 7, 2026 and April 23, 2026.

## Code Flow

### Step 1: Data Extraction
```python
mask = regime_mask
wind_sp = wind_speed50_clean[mask].to_numpy()
temp = temperature50_clean[mask].to_numpy()
regime_indices = np.where(mask)[0]  # Get indices for this regime
valid = ~(np.isnan(wind_sp) | np.isnan(temp))
wind_sp, temp = wind_sp[valid], temp[valid]
valid_indices = regime_indices[valid]  # Get the actual indices of valid points
```

**Purpose:** Extract the data subset for the current regime and track the original indices.

---

### Step 2: KDE Contour Generation
```python
kde = gaussian_kde(np.vstack([wind_sp, temp]))
x = np.linspace(wind_sp.min(), wind_sp.max(), 100)
y = np.linspace(temp.min(), temp.max(), 100)
X, Y = np.meshgrid(x, y)
Z = kde(np.vstack([X.ravel(), Y.ravel()])).reshape(X.shape)

cf = ax.contourf(X, Y, Z, levels=15, cmap='viridis', alpha=0.7)
contours = ax.contour(X, Y, Z, levels=15, colors='w', linewidths=0.6, zorder=3)
```

**Purpose:** Generate the KDE and draw both filled and outlined contours at 15 levels.

---

### Step 3: Outer Contour Extraction
```python
outer_contour = contours.collections[0]  # First contour is the outermost
outer_path = outer_contour.get_paths()
```

**Important Detail:**
- `contours.collections[0]` gets the outermost contour (lowest density level)
- This represents the boundary of the main data distribution
- Points outside this contour are considered potential outliers

---

### Step 4: Outlier Detection
```python
if outer_path:
    outer_contour_path = outer_path[0]
    inside = outer_contour_path.contains_points(np.column_stack([wind_sp, temp]))
    outlier_mask = ~inside
```

**Algorithm:**
1. `contains_points()` tests which data points fall within the outer contour polygon
2. `~inside` creates a boolean mask of points OUTSIDE the contour
3. This mask identifies potential outliers based on the KDE distribution

---

### Step 5: Date-Based Filtering
```python
target_dates = [np.datetime64('2026-05-07'), np.datetime64('2026-04-23')]
date_outlier_mask = np.zeros(len(valid_indices), dtype=bool)

for idx, valid_idx in enumerate(valid_indices):
    if time.iloc[valid_idx].date() in [d.astype('datetime64[D]').astype(object) for d in target_dates]:
        date_outlier_mask[idx] = outlier_mask[idx]
```

**Purpose:**
1. Iterate through each valid data point
2. Check if the timestamp matches May 7 or April 23, 2026
3. Mark as a date-specific outlier ONLY if it's both:
   - An outlier (outside the outer contour), AND
   - Occurs on one of the target dates

---

### Step 6: Visualization
```python
# Plot all points in green
ax.scatter(wind_sp, temp, s=5, c='g', edgecolor='k', linewidth=0.3, alpha=0.7, zorder=2)

# Highlight date-specific outliers in red
if np.any(date_outlier_mask):
    ax.scatter(wind_sp[date_outlier_mask], temp[date_outlier_mask], 
              s=150, c='red', marker='*', edgecolor='darkred', linewidth=1.5, 
              alpha=0.9, zorder=4, label=f'Outliers (May 7 & Apr 23)')
    ax.legend(loc='best', fontsize=9)
```

**Visual Hierarchy:**
- **zorder=2:** Green points (base layer)
- **zorder=3:** Contour lines (middle layer)
- **zorder=4:** Red stars (top layer, most visible)

**Star Markers:**
- Size: 150 (large, highly visible)
- Color: Red (#ff0000)
- Edge Color: Dark red for contrast
- Edge Width: 1.5pt
- Alpha: 0.9 (slightly transparent for visual interest)

---

## Key Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `levels` (contour) | 15 | Number of contour levels for smooth distribution |
| `s` (green points) | 5 | Small size for baseline data visibility |
| `s` (red stars) | 150 | Large size for emphasis on highlighted outliers |
| `marker` (outliers) | '*' | Star shape for instant visual recognition |
| `zorder` (green) | 2 | Below contours |
| `zorder` (contours) | 3 | Middle layer |
| `zorder` (red stars) | 4 | Always visible on top |
| `alpha` (green) | 0.7 | Slightly transparent |
| `alpha` (stars) | 0.9 | Nearly opaque for clarity |

---

## Date Conversion Logic

```python
d.astype('datetime64[D]').astype(object)
```

This chain of conversions:
1. `numpy.datetime64('2026-05-07')` → datetime64[ns] (nanosecond precision)
2. `.astype('datetime64[D]')` → datetime64[D] (day precision)
3. `.astype(object)` → Python date object (for comparison with `time.iloc[...].date()`)

This ensures consistent date comparisons between NumPy datetime64 and Python datetime.date objects.

---

## Plots Modified

### Plot 1: Wind Speed vs Temperature
- **X-axis:** Wind Speed @ 50m [m/s]
- **Y-axis:** Temperature @ 50m [deg C]
- **Lines:** 180-232

### Plot 2: Turbulence Intensity vs Wind Speed
- **X-axis:** Wind Speed @ 50m [m/s]
- **Y-axis:** Turbulence Intensity @ 50m
- **Lines:** 245-279

---

## Expected Behavior

### When Outliers Exist on Target Dates:
- Red stars appear on the plot overlapping the KDE distribution
- Legend shows "Outliers (May 7 & Apr 23)"
- Title includes note about red stars

### When No Outliers Exist on Target Dates:
- Only green points visible
- No legend added
- Plot otherwise unchanged from original

---

## Testing Recommendations

1. **Visual Inspection:** Run the script and look for red stars on the plots
2. **Date Verification:** Check if highlighted points correspond to May 7 or April 23, 2026
3. **Contour Validation:** Ensure red stars are distinctly outside the outer white contour line
4. **Console Output:** Look for any matplotlib warnings about path operations
