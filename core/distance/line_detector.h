#ifndef LINE_DETECTOR_H
#define LINE_DETECTOR_H

#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SUCCESS 1
#define FAIL 0
#define MAX_CANDIDATES 64

typedef struct {
    int x;
    int y;
    int valid;
} LinePosition;

typedef struct {
    int candidates_x[MAX_CANDIDATES];
    int candidates_y[MAX_CANDIDATES];
    int count_x;
    int count_y;
} CandidatePoints;

int gaussian_blur_uint8(const uint8_t* input, uint8_t* output, int width, int height);
int sobel_edge_detection(const uint8_t* input, uint8_t* output, int width, int height);
int compute_vertical_projection(const uint8_t* edge_data, float* projection, int width, int height);
int compute_horizontal_projection(const uint8_t* edge_data, float* projection, int width, int height);
int find_peaks_simple(const float* projection, int length, int* peaks, int max_peaks, float threshold_ratio);
int find_peaks_weighted(const float* projection, int length, int* raw_peaks, float* weighted_peaks, int max_peaks, float threshold_ratio);
int analyze_dark_regions(const uint8_t* gray_data, int width, int height, int* dark_col, int* dark_row, int edge_margin);
int filter_outliers_iqr(int* values, int count, int* filtered, int max_filtered);
int compute_median(int* values, int count);

int detect_lines_multi_strategy(
    const uint8_t* gray_data,
    int width,
    int height,
    int edge_margin,
    int* out_vertical_px,
    int* out_horizontal_px
);

float pixels_to_mm(int pixels, int dpi);

#ifdef __cplusplus
}
#endif

#endif
