# Experiment Report: fullfact_leardi

## Experiment Overview

| Property | Value |
| --- | --- |
| **Experiment ID** | 78efcfc9-5c66-4346-8631-9985f3e3b953 |
| **Name** | fullfact_leardi |
| **Design Type** | full_factorial |
| **Description** | N/A |
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

- **Design ID**: 64a37490-b6e3-4090-8bdf-00039cf6b631
- **Design Type**: full_factorial
- **Total Runs**: 8
- **Randomization**: False

| Run ID | Run Number | A | B | C |
| --- | --- | --- | --- | --- |
| 24a2e4fe-7de1-4997-b7e7-4af0d7374f29 | 1 | 9.0 | 3.6 | 9.0 |
| b494014b-17e1-4ce3-80ac-a6b56380abb1 | 2 | 9.0 | 3.6 | 11.0 |
| 8cd32d13-1357-4d6f-a954-197a1af7664c | 3 | 9.0 | 4.4 | 9.0 |
| b2a1ad54-57ad-4a60-8cbe-fa6ebf13c7f8 | 4 | 9.0 | 4.4 | 11.0 |
| e5469126-e832-401d-a1eb-a236e05766d4 | 5 | 11.0 | 3.6 | 9.0 |
| a04eee02-c00e-4516-9d04-9673465d7d0f | 6 | 11.0 | 3.6 | 11.0 |
| e3f73726-d3b1-4178-81ce-f9b128ed901f | 7 | 11.0 | 4.4 | 9.0 |
| 5883c20e-ba1e-4aea-bcd9-6e06907cc7c6 | 8 | 11.0 | 4.4 | 11.0 |

## Experimental Results

- **Results ID**: res_1471947c
- **Completeness**: complete
- **Recorded Entries**: 8

| Run Reference | viscosity | Status |
| --- | --- | --- |
| 24a2e4fe-7de1-4997-b7e7-4af0d7374f29 | 51.8 | complete |
| b494014b-17e1-4ce3-80ac-a6b56380abb1 | 50.2 | complete |
| 8cd32d13-1357-4d6f-a954-197a1af7664c | 51 | complete |
| b2a1ad54-57ad-4a60-8cbe-fa6ebf13c7f8 | 52 | complete |
| e5469126-e832-401d-a1eb-a236e05766d4 | 51.6 | complete |
| a04eee02-c00e-4516-9d04-9673465d7d0f | 46.6 | complete |
| e3f73726-d3b1-4178-81ce-f9b128ed901f | 42.4 | complete |
| 5883c20e-ba1e-4aea-bcd9-6e06907cc7c6 | 50 | complete |

## Statistical Analysis

- **Analysis ID**: ana_0a3c0696
- **Model Type**: interaction
- **R²**: 0.839208
- **Adjusted R²**: 0.0

### Coefficients

| Term | Estimate | P-Value |
| --- | --- | --- |
| Intercept | 49.45 | 0.016089 |
| A | -1.8 | 0.38642 |
| B | -0.6 | 0.7151 |
| C | 0.25 | 0.874334 |
| A:B | -0.85 | 0.619826 |
| A:C | 0.4 | 0.802837 |
| B:C | 1.9 | 0.370452 |

### ANOVA Table

| Source | Sum of Squares (SS) | DF | Mean Square (MS) | F-Value | P-Value |
| --- | --- | --- | --- | --- | --- |
| Model | 65.24 | 6 | 10.873333 | 0.869867 | 0.675148 |
| Residuals | 12.5 | 1 | 12.5 | N/A | N/A |
| Total | 77.74 | 7 | N/A | N/A | N/A |
