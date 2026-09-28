# Re-analysis summary (fixed pipeline, unfiltered strain)

## Static plateau (mean principal strain, hold window 5 s after onset to 1 s before release, capped at 25 s)

| name                   |   well |   pressure |   plateau |   hold_end_s |   drift |   rise_10_90 |   n_triangles |
|:-----------------------|-------:|-----------:|----------:|-------------:|--------:|-------------:|--------------:|
| 20241003_2_50_cont_HD  |      2 |         50 |    0.1319 |      21.6000 |  0.0285 |       0.0000 |            10 |
| 20241003_4_50_cont_HD  |      4 |         50 |    0.0846 |      29.0000 |  0.0005 |       0.1601 |            18 |
| 20241003_5_50_cont_HD  |      5 |         50 |    0.0983 |      26.1000 | -0.0032 |       1.1207 |            14 |
| 20241003_6_50_cont_HD  |      6 |         50 |    0.1094 |      22.2000 | -0.0649 |       0.0000 |             9 |
| 20241003_2_100_cont_HD |      2 |        100 |    0.1520 |      28.8000 |  0.0204 |       1.0207 |            10 |
| 20241003_5_100_cont_HD |      5 |        100 |    0.0949 |      28.5000 |  0.0113 |       2.3816 |            14 |
| 20241003_6_100_cont_HD |      6 |        100 |    0.1069 |      27.3000 |  0.0075 |       0.1401 |             6 |
| 20241003_2_200_cont_HD |      2 |        200 |    0.1420 |      29.4000 |  0.0165 |       1.4810 |             9 |
| 20241003_4_200_cont_HD |      4 |        200 |    0.1009 |      26.1000 | -0.0334 |       0.3202 |             3 |
| 20241003_5_200_cont_HD |      5 |        200 |    0.1208 |      14.6000 | -0.0000 |       1.9613 |            12 |

## Static per-pressure summary (n = membranes)

|   pressure |   count |   mean |    std |
|-----------:|--------:|-------:|-------:|
|         50 |  4.0000 | 0.1061 | 0.0200 |
|        100 |  3.0000 | 0.1179 | 0.0301 |
|        200 |  3.0000 | 0.1212 | 0.0206 |

## 200 mbar diagnosis

- 20241003_2_200_cont_HD: measured pressure depth -200.1 mbar; per-triangle plateau strains: [0.122, 0.123, 0.141, 0.143, 0.146, 0.15, 0.153, 0.16, 0.163]

- 20241003_4_200_cont_HD: measured pressure depth -199.8 mbar; per-triangle plateau strains: [0.089, 0.092, 0.102]

- 20241003_5_200_cont_HD: measured pressure depth -199.8 mbar; per-triangle plateau strains: [0.083, 0.095, 0.113, 0.116, 0.121, 0.124, 0.125, 0.126, 0.13, 0.133, 0.139, 0.165]

## Cyclic metrics (plateau means; t=0 at first vacuum onset)

| name                       |   well |   pressure |   cycle1 |   cycle2 |   cycle_diff |   residual_after_c1 |   residual_after_c2 |   rise_10_90 |
|:---------------------------|-------:|-----------:|---------:|---------:|-------------:|--------------------:|--------------------:|-------------:|
| 20241016_cyclic_1_50 mbar  |      1 |         50 |   0.0957 |   0.1288 |       0.0331 |              0.0495 |              0.0465 |       0.0000 |
| 20241016_cyclic_2_50 mbar  |      2 |         50 |   0.1202 |   0.1293 |       0.0091 |              0.0179 |              0.0181 |       1.8006 |
| 20241017_cyclic_3_50 mbar  |      3 |         50 |   0.1105 |   0.1186 |       0.0081 |              0.0122 |              0.0176 |       0.0000 |
| 20241017_cyclic_4_50 mbar  |      4 |         50 |   0.1637 |   0.1716 |       0.0079 |              0.0904 |              0.0958 |       0.0000 |
| 20241016_cyclic_1_100 mbar |      1 |        100 |   0.0873 |   0.1132 |       0.0259 |              0.0020 |             -0.0005 |       0.0000 |
| 20241016_cyclic_2_100 mbar |      2 |        100 |   0.1158 |   0.1203 |       0.0045 |              0.0157 |              0.0088 |       0.0000 |
| 20241017_cyclic_3_100 mbar |      3 |        100 |   0.1503 |   0.1490 |      -0.0013 |              0.0344 |              0.1622 |       0.0000 |
| 20241017_cyclic_4_100 mbar |      4 |        100 |   0.1472 |   0.1711 |       0.0240 |              0.0941 |              0.0730 |       0.0000 |
| 20241016_cyclic_1_200 mbar |      1 |        200 |   0.1101 |   0.1190 |       0.0089 |              0.0288 |              0.0362 |       0.0000 |
| 20241016_cyclic_2_200 mbar |      2 |        200 |   0.0926 |   0.1088 |       0.0162 |              0.0482 |              0.0019 |       0.0000 |
| 20241017_cyclic_3_200 mbar |      3 |        200 |   0.0948 |   0.1048 |       0.0100 |              0.0445 |              0.1077 |       0.0000 |
| 20241017_cyclic_4_200 mbar |      4 |        200 |   0.1515 |   0.1532 |       0.0017 |              0.0684 |              0.0712 |       0.0000 |

## Cyclic per-pressure summary

|   pressure |   ('cycle1', 'count') |   ('cycle1', 'mean') |   ('cycle1', 'std') |   ('cycle2', 'count') |   ('cycle2', 'mean') |   ('cycle2', 'std') |   ('cycle_diff', 'count') |   ('cycle_diff', 'mean') |   ('cycle_diff', 'std') |   ('residual_after_c1', 'count') |   ('residual_after_c1', 'mean') |   ('residual_after_c1', 'std') |
|-----------:|----------------------:|---------------------:|--------------------:|----------------------:|---------------------:|--------------------:|--------------------------:|-------------------------:|------------------------:|---------------------------------:|--------------------------------:|-------------------------------:|
|         50 |                4.0000 |               0.1225 |              0.0292 |                4.0000 |               0.1371 |              0.0236 |                    4.0000 |                   0.0146 |                  0.0124 |                           4.0000 |                          0.0425 |                         0.0359 |
|        100 |                4.0000 |               0.1251 |              0.0296 |                4.0000 |               0.1384 |              0.0267 |                    4.0000 |                   0.0133 |                  0.0137 |                           4.0000 |                          0.0366 |                         0.0406 |
|        200 |                4.0000 |               0.1123 |              0.0273 |                4.0000 |               0.1215 |              0.0220 |                    4.0000 |                   0.0092 |                  0.0059 |                           4.0000 |                          0.0475 |                         0.0163 |

## Pneumatic settling time (measured pressure, 10-90% of the achieved depth)

The cyclic records are sampled at ~2 Hz and resolve this; the static records at ~1 Hz are at the edge of usability and are reported for completeness only.

| name                       | regime   |   pressure |   depth_mbar |   t10_90_s |   sampling_dt_s |
|:---------------------------|:---------|-----------:|-------------:|-----------:|----------------:|
| 20241016_cyclic_1_50 mbar  | cyclic   |         50 |        49.86 |       1.28 |            0.51 |
| 20241016_cyclic_2_50 mbar  | cyclic   |         50 |        49.86 |       1.10 |            0.51 |
| 20241017_cyclic_3_50 mbar  | cyclic   |         50 |        49.86 |       0.86 |            0.39 |
| 20241017_cyclic_4_50 mbar  | cyclic   |         50 |        49.86 |       2.66 |            0.56 |
| 20241016_cyclic_1_100 mbar | cyclic   |        100 |        99.73 |       1.77 |            0.49 |
| 20241016_cyclic_2_100 mbar | cyclic   |        100 |        99.73 |       1.90 |            0.51 |
| 20241017_cyclic_3_100 mbar | cyclic   |        100 |        99.73 |       2.04 |            0.50 |
| 20241017_cyclic_4_100 mbar | cyclic   |        100 |        99.73 |       6.35 |            0.78 |
| 20241016_cyclic_1_200 mbar | cyclic   |        200 |       193.14 |       4.93 |            0.49 |
| 20241016_cyclic_2_200 mbar | cyclic   |        200 |       182.57 |       5.79 |            0.56 |
| 20241017_cyclic_3_200 mbar | cyclic   |        200 |       199.77 |       4.53 |            0.52 |
| 20241017_cyclic_4_200 mbar | cyclic   |        200 |       199.77 |       5.00 |            0.75 |
| 20241003_2_50_cont_HD      | static   |         50 |        49.86 |       6.78 |            1.11 |
| 20241003_4_50_cont_HD      | static   |         50 |        49.86 |       2.06 |            1.08 |
| 20241003_5_50_cont_HD      | static   |         50 |        49.86 |      10.98 |            0.58 |
| 20241003_6_50_cont_HD      | static   |         50 |        49.86 |       8.37 |            0.62 |
| 20241003_2_100_cont_HD     | static   |        100 |        99.73 |       1.50 |            0.83 |
| 20241003_5_100_cont_HD     | static   |        100 |        99.73 |       0.00 |            0.72 |
| 20241003_6_100_cont_HD     | static   |        100 |        99.73 |       2.92 |            0.83 |
| 20241003_2_200_cont_HD     | static   |        200 |       199.77 |       4.20 |            0.45 |
| 20241003_4_200_cont_HD     | static   |        200 |       199.77 |       6.05 |            0.76 |
| 20241003_5_200_cont_HD     | static   |        200 |       199.77 |      11.44 |            0.76 |

|                 |   count |   mean |   std |
|:----------------|--------:|-------:|------:|
| ('cyclic', 50)  |    4.00 |   1.48 |  0.81 |
| ('cyclic', 100) |    4.00 |   3.02 |  2.23 |
| ('cyclic', 200) |    4.00 |   5.06 |  0.53 |
| ('static', 50)  |    4.00 |   7.05 |  3.75 |
| ('static', 100) |    3.00 |   1.47 |  1.46 |
| ('static', 200) |    3.00 |   7.23 |  3.76 |

## Equibiaxiality: principal-strain ratio e2/e1 (plateau-averaged per triangle) and orientation concentration

orientation_resultant: circular resultant of the doubled principal-axis angles; 0 = no preferred direction (equibiaxial), 1 = fully aligned.

| name                       | regime   |   well |   pressure |   n_triangles |   ratio_median |   ratio_q1 |   ratio_q3 |   orientation_resultant |
|:---------------------------|:---------|-------:|-----------:|--------------:|---------------:|-----------:|-----------:|------------------------:|
| 20241016_cyclic_1_50 mbar  | cyclic   |      1 |         50 |             7 |          0.497 |      0.287 |      0.643 |                   0.694 |
| 20241016_cyclic_2_50 mbar  | cyclic   |      2 |         50 |            12 |          0.412 |      0.370 |      0.580 |                   0.950 |
| 20241017_cyclic_3_50 mbar  | cyclic   |      3 |         50 |            11 |          0.056 |      0.014 |      0.093 |                   0.854 |
| 20241017_cyclic_4_50 mbar  | cyclic   |      4 |         50 |             9 |          0.213 |      0.196 |      0.309 |                   0.918 |
| 20241016_cyclic_1_100 mbar | cyclic   |      1 |        100 |             6 |          0.291 |      0.053 |      0.661 |                   0.519 |
| 20241016_cyclic_2_100 mbar | cyclic   |      2 |        100 |            12 |          0.240 |      0.219 |      0.512 |                   0.966 |
| 20241017_cyclic_3_100 mbar | cyclic   |      3 |        100 |            11 |          0.162 |      0.070 |      0.273 |                   0.916 |
| 20241017_cyclic_4_100 mbar | cyclic   |      4 |        100 |             6 |          0.315 |      0.222 |      0.353 |                   0.950 |
| 20241016_cyclic_1_200 mbar | cyclic   |      1 |        200 |             7 |          0.409 |      0.320 |      0.474 |                   0.696 |
| 20241016_cyclic_2_200 mbar | cyclic   |      2 |        200 |            10 |          0.208 |      0.098 |      0.336 |                   0.936 |
| 20241017_cyclic_3_200 mbar | cyclic   |      3 |        200 |            11 |         -0.090 |     -0.285 |      0.001 |                   0.510 |
| 20241017_cyclic_4_200 mbar | cyclic   |      4 |        200 |             8 |          0.135 |      0.088 |      0.191 |                   0.889 |
| 20241003_2_50_cont_HD      | static   |      2 |         50 |            10 |          0.775 |      0.628 |      0.869 |                   0.392 |
| 20241003_4_50_cont_HD      | static   |      4 |         50 |            18 |          0.616 |      0.452 |      0.693 |                   0.522 |
| 20241003_5_50_cont_HD      | static   |      5 |         50 |            14 |          0.426 |      0.275 |      0.554 |                   0.660 |
| 20241003_6_50_cont_HD      | static   |      6 |         50 |             9 |          0.609 |      0.370 |      0.729 |                   0.582 |
| 20241003_2_100_cont_HD     | static   |      2 |        100 |            10 |          0.754 |      0.641 |      0.820 |                   0.602 |
| 20241003_5_100_cont_HD     | static   |      5 |        100 |            14 |          0.172 |      0.032 |      0.347 |                   0.660 |
| 20241003_6_100_cont_HD     | static   |      6 |        100 |             6 |          0.263 |      0.189 |      0.275 |                   0.974 |
| 20241003_2_200_cont_HD     | static   |      2 |        200 |             9 |          0.484 |      0.400 |      0.552 |                   0.839 |
| 20241003_4_200_cont_HD     | static   |      4 |        200 |             3 |          0.590 |      0.526 |      0.648 |                   0.592 |
| 20241003_5_200_cont_HD     | static   |      5 |        200 |            12 |          0.618 |      0.560 |      0.703 |                   0.174 |

## Post-release relaxation fits (eps = eps_inf + A*exp(-t/tau))

valid=False: fit hit the tau bound or A<=0 (window contaminated by the next pulse or non-exponential).

| name                       |   well |   pressure | rest   |   tau_s |   amplitude |   residual_inf |   rmse | valid   |
|:---------------------------|-------:|-----------:|:-------|--------:|------------:|---------------:|-------:|:--------|
| 20241016_cyclic_1_50 mbar  |      1 |         50 | rest1  |  60.000 |      -0.104 |          0.138 |  0.016 | False   |
| 20241016_cyclic_1_50 mbar  |      1 |         50 | rest2  |   0.679 |       0.022 |          0.046 |  0.001 | True    |
| 20241016_cyclic_1_100 mbar |      1 |        100 | rest1  |   1.715 |       0.010 |         -0.002 |  0.003 | True    |
| 20241016_cyclic_1_100 mbar |      1 |        100 | rest2  |   8.688 |       0.031 |         -0.019 |  0.003 | True    |
| 20241016_cyclic_1_200 mbar |      1 |        200 | rest1  |  60.000 |      -0.240 |          0.237 |  0.027 | False   |
| 20241016_cyclic_1_200 mbar |      1 |        200 | rest2  |   1.419 |       0.012 |          0.035 |  0.001 | True    |
| 20241016_cyclic_2_50 mbar  |      2 |         50 | rest1  |   0.783 |       0.039 |          0.013 |  0.017 | True    |
| 20241016_cyclic_2_50 mbar  |      2 |         50 | rest2  |  10.310 |       0.106 |         -0.050 |  0.004 | True    |
| 20241016_cyclic_2_100 mbar |      2 |        100 | rest1  |   1.295 |       0.054 |          0.011 |  0.024 | True    |
| 20241016_cyclic_2_100 mbar |      2 |        100 | rest2  |   3.050 |       0.061 |         -0.006 |  0.004 | True    |
| 20241016_cyclic_2_200 mbar |      2 |        200 | rest1  |  60.000 |      -0.435 |          0.432 |  0.033 | False   |
| 20241016_cyclic_2_200 mbar |      2 |        200 | rest2  |   0.650 |       0.051 |          0.001 |  0.004 | True    |
| 20241017_cyclic_3_50 mbar  |      3 |         50 | rest1  |   3.841 |       0.060 |          0.000 |  0.002 | True    |
| 20241017_cyclic_3_50 mbar  |      3 |         50 | rest2  |   1.169 |       0.047 |          0.015 |  0.003 | True    |
| 20241017_cyclic_3_100 mbar |      3 |        100 | rest1  |   1.580 |       0.058 |          0.032 |  0.002 | True    |
| 20241017_cyclic_3_100 mbar |      3 |        100 | rest2  |   0.962 |      -0.013 |          0.162 |  0.001 | False   |
| 20241017_cyclic_3_200 mbar |      3 |        200 | rest1  |   5.361 |       0.064 |          0.025 |  0.018 | True    |
| 20241017_cyclic_3_200 mbar |      3 |        200 | rest2  |   2.842 |      -0.003 |          0.108 |  0.001 | False   |
| 20241017_cyclic_4_50 mbar  |      4 |         50 | rest1  |  18.001 |       0.081 |          0.037 |  0.002 | True    |
| 20241017_cyclic_4_50 mbar  |      4 |         50 | rest2  |   2.744 |       0.030 |          0.089 |  0.001 | True    |
| 20241017_cyclic_4_100 mbar |      4 |        100 | rest1  |  60.000 |      -0.278 |          0.335 |  0.038 | False   |
| 20241017_cyclic_4_100 mbar |      4 |        100 | rest2  |   3.508 |       0.056 |          0.056 |  0.002 | True    |
| 20241017_cyclic_4_200 mbar |      4 |        200 | rest1  |  60.000 |      -0.211 |          0.251 |  0.040 | False   |
| 20241017_cyclic_4_200 mbar |      4 |        200 | rest2  |   3.577 |       0.053 |          0.055 |  0.003 | True    |

Valid fits (n = 17/24): median tau = 2.74 s (IQR 1.29-3.84 s); median extrapolated residual eps_inf = 0.0154.

## Dense field vs landmarks (plateau means, hold window)

valid=False: quiet-window mean biased (|bias| >= 3%) or per-triangle noise floor >= 5% — insufficient speckle contrast (patches follow illumination, not material); excluded from claims and maps. quiet_sd is reported but not gated: in cyclic records the pre-onset window contains genuine recovery drift from the preceding pressure level of the sequential protocol.

Cross-validation over the 13 valid runs: Pearson r = 0.720, median bias (dense - landmark) = -0.0064 strain, mean |bias| = 0.0132. radial_slope: linear strain change from center (r=0) to ring (r=R). radial_change and radial_change_ci: the same fit expressed over the analyzed span only, with its 95% interval (Figure 6). ratio_median: dense-field principal-strain ratio e2/e1.

| name                       | regime   |   well |   pressure |   n_triangles |   quiet_bias |   quiet_sd |   tri_noise | valid   |   dense_plateau |   landmark_plateau |    bias |   central_sd |   radial_slope |   radial_change |   radial_change_ci |   ratio_median |
|:---------------------------|:---------|-------:|-----------:|--------------:|-------------:|-----------:|------------:|:--------|----------------:|-------------------:|--------:|-------------:|---------------:|----------------:|-------------------:|---------------:|
| 20241016_cyclic_1_50 mbar  | cyclic   |      1 |         50 |            72 |       0.0004 |     0.0245 |      0.0446 | True    |          0.0864 |             0.0964 | -0.0100 |       0.1427 |         0.0807 |          0.0575 |             0.1278 |        -0.0830 |
| 20241016_cyclic_2_50 mbar  | cyclic   |      2 |         50 |            77 |      -0.0076 |     0.0220 |      0.0275 | True    |          0.1038 |             0.1207 | -0.0170 |       0.0418 |        -0.0008 |         -0.0006 |             0.0426 |         0.2012 |
| 20241017_cyclic_3_50 mbar  | cyclic   |      3 |         50 |            63 |      -0.0177 |     0.0112 |      0.0173 | True    |          0.0890 |             0.1090 | -0.0200 |       0.0615 |         0.0149 |          0.0117 |             0.0629 |        -0.0792 |
| 20241017_cyclic_4_50 mbar  | cyclic   |      4 |         50 |           100 |       0.0123 |     0.0625 |      0.0871 | False   |          0.2972 |             0.1611 |  0.1361 |       0.5656 |        -0.2640 |         -0.1842 |             0.4027 |        -0.3812 |
| 20241016_cyclic_1_100 mbar | cyclic   |      1 |        100 |            96 |      -0.0003 |     0.0204 |      0.0410 | True    |          0.0824 |             0.0874 | -0.0051 |       0.1832 |         0.0702 |          0.0479 |             0.1308 |        -0.1755 |
| 20241016_cyclic_2_100 mbar | cyclic   |      2 |        100 |            70 |       0.0046 |     0.0296 |      0.0334 | True    |          0.1120 |             0.1158 | -0.0038 |       0.0839 |         0.1248 |          0.0903 |             0.0720 |         0.1129 |
| 20241017_cyclic_3_100 mbar | cyclic   |      3 |        100 |            59 |      -0.0054 |     0.0052 |      0.0173 | True    |          0.1352 |             0.1477 | -0.0125 |       0.0594 |        -0.0360 |         -0.0248 |             0.0496 |         0.0439 |
| 20241017_cyclic_4_100 mbar | cyclic   |      4 |        100 |            99 |       0.1003 |     0.1384 |      0.1380 | False   |          0.3157 |             0.1453 |  0.1704 |       0.3118 |         0.8614 |          0.6089 |             0.4524 |        -0.1962 |
| 20241016_cyclic_1_200 mbar | cyclic   |      1 |        200 |            52 |       0.0102 |     0.0393 |      0.0566 | False   |          0.1222 |             0.1113 |  0.0108 |       0.2369 |         0.3058 |          0.1776 |             0.2524 |        -0.1561 |
| 20241016_cyclic_2_200 mbar | cyclic   |      2 |        200 |           128 |       0.1130 |     0.1643 |      0.0888 | False   |          0.3372 |             0.0918 |  0.2454 |       0.7835 |        -0.5533 |         -0.4133 |             0.4894 |        -0.2828 |
| 20241017_cyclic_3_200 mbar | cyclic   |      3 |        200 |           125 |       0.0107 |     0.0412 |      0.0862 | False   |          0.1321 |             0.0946 |  0.0375 |       0.3210 |         0.1275 |          0.0986 |             0.2363 |        -0.4088 |
| 20241017_cyclic_4_200 mbar | cyclic   |      4 |        200 |            74 |       0.0712 |     0.1001 |      0.1328 | False   |          0.2276 |             0.1502 |  0.0775 |       0.4134 |        -0.6586 |         -0.4628 |             0.3060 |        -0.2974 |
| 20241003_2_50_cont_HD      | static   |      2 |         50 |           128 |      -0.0012 |     0.0021 |      0.0129 | True    |          0.1254 |             0.1319 | -0.0064 |       0.0640 |         0.0645 |          0.0506 |             0.0542 |         0.2930 |
| 20241003_4_50_cont_HD      | static   |      4 |         50 |            25 |      -0.0038 |     0.0068 |      0.0125 | True    |          0.0869 |             0.0846 |  0.0023 |       0.0398 |        -0.0407 |         -0.0275 |             0.0988 |         0.2881 |
| 20241003_5_50_cont_HD      | static   |      5 |         50 |            46 |       0.0002 |     0.0007 |      0.0058 | True    |          0.1022 |             0.0983 |  0.0040 |       0.0997 |         0.0741 |          0.0475 |             0.1080 |         0.2962 |
| 20241003_6_50_cont_HD      | static   |      6 |         50 |            48 |      -0.0015 |     0.0021 |      0.0128 | True    |          0.1281 |             0.1094 |  0.0187 |       0.0482 |         0.0634 |          0.0488 |             0.0543 |         0.2944 |
| 20241003_2_100_cont_HD     | static   |      2 |        100 |            98 |      -0.0011 |     0.0019 |      0.0145 | True    |          0.1354 |             0.1520 | -0.0166 |       0.0489 |        -0.0397 |         -0.0302 |             0.0478 |         0.2287 |
| 20241003_5_100_cont_HD     | static   |      5 |        100 |            25 |       0.0199 |     0.0218 |      0.0654 | False   |          0.0680 |             0.0949 | -0.0269 |       0.1931 |         0.3215 |          0.2280 |             0.2960 |        -0.3012 |
| 20241003_6_100_cont_HD     | static   |      6 |        100 |            30 |      -0.0027 |     0.0081 |      0.0616 | False   |          0.0961 |             0.1069 | -0.0108 |       0.0844 |         0.1207 |          0.0765 |             0.0956 |        -0.0745 |
| 20241003_2_200_cont_HD     | static   |      2 |        200 |            87 |      -0.0014 |     0.0032 |      0.0173 | True    |          0.1219 |             0.1420 | -0.0202 |       0.0485 |        -0.1162 |         -0.0840 |             0.0654 |         0.1241 |
| 20241003_4_200_cont_HD     | static   |      4 |        200 |            66 |      -0.0000 |     0.0013 |      0.0187 | True    |          0.1365 |             0.1009 |  0.0356 |       0.1216 |         0.5756 |          0.3788 |             0.3833 |        -0.3505 |
| 20241003_5_200_cont_HD     | static   |      5 |        200 |            69 |       0.0272 |     0.0373 |      0.0872 | False   |          0.1584 |             0.1208 |  0.0376 |       0.1470 |         0.3384 |          0.2256 |             0.2497 |        -0.2005 |

## Sampling-density check

Across the 13 valid dense fields, the correlation between element count and plateau strain is r = 0.239.

Across the 10 static landmark runs, the correlation between triangle count and plateau strain is r = -0.314.

Bootstrap (500 draws) subsampling membrane 2's dense field (128 elements, full mean 0.1329) down to membrane 4's element count (25): mean 0.1334, 95% interval [0.1078, 0.1615]. Sparse sampling widens the interval but does not bias the estimate.

## Radial strain at maximum deformation (static 50 mbar, all markers, center from all-marker similarity fit)

| name                  |      n |   radial_mean |   radial_sd |   dtheta_mean |   dtheta_sd |   dtheta_max |
|:----------------------|-------:|--------------:|------------:|--------------:|------------:|-------------:|
| 20241003_2_50_cont_HD | 10.000 |         0.189 |       0.021 |         1.583 |       1.287 |        5.024 |
| 20241003_4_50_cont_HD | 15.000 |         0.133 |       0.023 |         0.774 |       0.569 |        2.456 |
| 20241003_5_50_cont_HD | 12.000 |         0.110 |       0.034 |         1.010 |       0.721 |        2.315 |
| 20241003_6_50_cont_HD |  9.000 |         0.201 |       0.064 |         1.773 |       1.498 |        5.365 |
