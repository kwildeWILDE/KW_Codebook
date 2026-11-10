# Visual Reference Guide - Highlighted KDE Plots

## Color & Marker Legend

### Elements on the Plots

```
┌─────────────────────────────────────────────────────────────┐
│  M2 Wind Speed vs Temperature Bivariate KDE @ 50m           │
│  (Red stars: Outliers on May 7 & Apr 23, 2026)             │
└─────────────────────────────────────────────────────────────┘

  ████████████████████  Viridis Colormap (PDF Density)
  ░ Light (low density)
  ░ Dark (high density)

  ─────────────────────  White Contour Lines (15 levels)
  ─────────────────────  Outermost contour = boundary for outlier detection

  ● ● ● ●  Green dots (size=5)
  All valid data points within the regime

  ★ ★ ★   Red stars (size=150, if present)
  Outliers from May 7 & April 23, 2026
  Positioned OUTSIDE the outermost white contour
```

---

## How to Interpret the Highlighting

### Green Points (●)
- **Meaning:** Normal observations within the regime
- **Size:** 5 pixels
- **Color:** Green with black edge
- **Transparency:** 0.7 (slightly transparent)
- **Layer:** Behind contours and stars

### White Contour Lines (─)
- **Meaning:** Boundaries of the KDE probability distribution
- **Number:** 15 levels from high to low density
- **Outermost line:** Separates outliers from main distribution
- **Layer:** Middle layer

### Red Stars (★)
- **Meaning:** OUTLIER observations on May 7 or April 23, 2026
- **Size:** 150 pixels (very large)
- **Color:** Red (#FF0000) with dark red edge
- **Shape:** 5-pointed star for maximum visibility
- **Transparency:** 0.9 (nearly opaque)
- **Position:** Should be OUTSIDE (beyond) the outermost white contour line
- **Layer:** On top, most visible

---

## Key Interpretation Rules

### Rule 1: Location Matters
```
        OUTLIER                    NORMAL
    (outside contour)          (inside contour)
    
    ★                    ●●●●●
     |                  ●●●●●●●
     └─────────         ●●●●●●●
            ═════════════════════
         (outermost contour line)
```

### Rule 2: Date-Specific Highlighting
- Only points from May 7, 2026 are marked with red stars
- Only points from April 23, 2026 are marked with red stars
- Other dates' outliers remain green (not highlighted)

### Rule 3: Dual Criteria
A point is highlighted RED if and only if BOTH conditions are true:
1. **It's an outlier:** Outside the outer contour ellipse
2. **It's from a target date:** May 7 or April 23, 2026

```
┌─────────────────────────────────────┐
│ Is this point an outlier?           │
│         ↙              ↖             │
│        YES              NO           │
│         ↓               ↓            │
│    Is it from     Remains green     │
│    target date?   (not highlighted) │
│     ↙      ↖                        │
│   YES      NO                       │
│    ↓       ↓                        │
│   RED★   GREEN●                    │
└─────────────────────────────────────┘
```

---

## What You Should See

### Plot 1: Wind Speed vs Temperature
```
Expected pattern:
- Viridis contours showing temperature vs wind speed relationship
- Most points clustered in green within the contour
- IF outliers exist on target dates → RED STARS visible outside the outer contour
- Title notes: "(Red stars: Outliers on May 7 & Apr 23, 2026)"
```

### Plot 2: Turbulence Intensity vs Wind Speed
```
Expected pattern:
- Viridis contours showing turbulence intensity vs wind speed relationship
- Dense green point cloud in the center
- IF outliers exist on target dates → RED STARS visible outside the outer contour
- Title notes: "(Red stars: Outliers on May 7 & Apr 23, 2026)"
```

---

## Quality Checklist

When viewing the plots, verify:

- [ ] Green points form the main cloud visible through contours
- [ ] 15 distinct white contour lines visible (some may be very close)
- [ ] Outermost white contour forms a clear boundary
- [ ] Red stars (if any) are clearly OUTSIDE the outermost white contour
- [ ] Red stars are much larger than green dots (easy to spot)
- [ ] Legend appears only when red stars are present
- [ ] Plot title includes date range note
- [ ] Both "Unstable" and "Stable" regimes shown side-by-side
- [ ] Colorbar (viridis) shows PDF values from low to high density

---

## Troubleshooting Visual Issues

### Problem: Can't see the red stars
**Solution:** They're only present if outliers from May 7 or Apr 23 exist in that regime

### Problem: Red stars seem to be inside the contour
**Solution:** Check if the point is actually beyond the outermost (whitest) contour line

### Problem: No red stars showing at all
**Possible causes:**
1. No outliers exist on those dates
2. Outliers exist but fall within the outer contour
3. Script ran but didn't regenerate the plots

### Problem: Too many red stars visible
**Expected:** Likely only a few (0-5) red stars per plot, as true outliers are rare

---

## Statistical Interpretation

### What Does "Outlier" Mean Here?
- Points with probability density below the main distribution boundary
- Represent unusual combinations of variables:
  - Unusual wind speed + temperature combinations
  - Unusual turbulence intensity + wind speed combinations
- Not necessarily measurement errors (though could be)
- Represent real but rare atmospheric conditions

### Why These Dates?
- May 7, 2026: Likely represents a specific weather event with extreme values
- April 23, 2026: Another atmospheric anomaly worth highlighting

### Stability Regimes
- **Unstable (Ri < 0):** Convective conditions, sun-heated surface
- **Stable (Ri > 0):** Stable conditions, radiative cooling, inversion layers

Outliers may have different characteristics in each regime due to different physical processes.

---

## Revision History
- **Version 1.0:** Initial implementation highlighting May 7 & Apr 23, 2026 outliers
- Plots modified: Lines 180-232 (Wind Speed vs Temperature)
- Plots modified: Lines 245-279 (Turbulence Intensity vs Wind Speed)
