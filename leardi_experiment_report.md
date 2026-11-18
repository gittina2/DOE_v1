# Experiment Report: leardi_experiment

## Experiment Overview

| Property | Value |
| --- | --- |
| **Experiment ID** | a150694a-8975-4497-9d0d-7c0e8b8d6f76 |
| **Name** | leardi_experiment |
| **Design Type** | full_factorial |
| **Description** | exp di prova basato sul paper di leardi nostro signore |
| **Schema Version** | 1.1 |
| **Current Workflow Step** | analysis_created |

## Factors & Responses

### Experimental Factors

| Factor Name | Type | Unit | Bounds / Levels |
| --- | --- | --- | --- |
| A | continuous | g | [9.0, 11.0] |
| B | continuous | g | [3.6, 4.4] |
| C | continuous | g | [9.0, 11.0] |

### Response Variables

| Response Name | Type | Unit |
| --- | --- | --- |
| viscosity | continuous | N/A |

## Experimental Design

- **Design ID**: 0d3fe7c2-364c-43fe-8db6-e23c0c244d2f
- **Design Type**: full_factorial
- **Total Runs**: 8
- **Randomization**: False

| Run ID | Run Number | A | B | C |
| --- | --- | --- | --- | --- |
| aa2d89dd-b460-4f95-8da0-dd070ba8de4d | 1 | 9.0 | 3.6 | 9.0 |
| 04122e81-f638-4317-b9b0-f59cb27f2651 | 2 | 9.0 | 3.6 | 11.0 |
| 5040b195-1a10-4e41-ab6e-51d15cdd8924 | 3 | 9.0 | 4.4 | 9.0 |
| 5e2dfb88-8dee-4907-9655-231f89315cbd | 4 | 9.0 | 4.4 | 11.0 |
| 7dfa6aef-9d00-440e-b314-7bbc9c141a02 | 5 | 11.0 | 3.6 | 9.0 |
| 84714627-fb75-43b5-a9ff-50e8935735f1 | 6 | 11.0 | 3.6 | 11.0 |
| b9fd7297-4dcc-47d6-9584-99d22ab7f110 | 7 | 11.0 | 4.4 | 9.0 |
| 378a0254-c2a9-47f6-a393-9793a74f002e | 8 | 11.0 | 4.4 | 11.0 |

## Experimental Results

- **Results ID**: res_8c299430
- **Completeness**: complete
- **Recorded Entries**: 8

| Run Reference | viscosity | Status |
| --- | --- | --- |
| aa2d89dd-b460-4f95-8da0-dd070ba8de4d | 51.8 | complete |
| 04122e81-f638-4317-b9b0-f59cb27f2651 | 50.2 | complete |
| 5040b195-1a10-4e41-ab6e-51d15cdd8924 | 51 | complete |
| 5e2dfb88-8dee-4907-9655-231f89315cbd | 52 | complete |
| 7dfa6aef-9d00-440e-b314-7bbc9c141a02 | 51.6 | complete |
| 84714627-fb75-43b5-a9ff-50e8935735f1 | 46.6 | complete |
| b9fd7297-4dcc-47d6-9584-99d22ab7f110 | 42.4 | complete |
| 378a0254-c2a9-47f6-a393-9793a74f002e | 50 | complete |

## Statistical Analysis

- **Analysis ID**: ana_58f9a068
- **Model Type**: linear
- **R²**: 0.376897
- **Adjusted R²**: 0.0

### Coefficients

| Term | Estimate | P-Value |
| --- | --- | --- |
| Intercept | 49.45 | 2e-06 |
| A | -1.8 | 0.217297 |
| B | -0.6 | 0.651307 |
| C | 0.25 | 0.848901 |

### ANOVA Table

| Source | Sum of Squares (SS) | DF | Mean Square (MS) | F-Value | P-Value |
| --- | --- | --- | --- | --- | --- |
| Model | 29.3 | 3 | 9.766667 | 0.806496 | 0.552351 |
| Residuals | 48.44 | 4 | 12.11 | N/A | N/A |
| Total | 77.74 | 7 | N/A | N/A | N/A |
