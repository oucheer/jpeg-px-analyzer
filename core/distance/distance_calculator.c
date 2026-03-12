#include "distance_calculator.h"
#include <math.h>
#include <stdlib.h>

float pixels_to_mm(int pixels, int dpi) {
    if (dpi <= 0) {
        dpi = 300;
    }
    float result = pixels * 25.4f / dpi;
    result = roundf(result * 10.0f) / 10.0f;
    return result;
}

int detect_horizontal_line(
    const uint8_t* binary_data,
    int width,
    int height,
    int* out_position
) {
    if (binary_data == NULL || width <= 0 || height <= 0 || out_position == NULL) {
        return FAIL;
    }

    float* vertical_projection = (float*)malloc(height * sizeof(float));
    if (vertical_projection == NULL) {
        return FAIL;
    }

    for (int y = 0; y < height; y++) {
        int sum = 0;
        for (int x = 0; x < width; x++) {
            int idx = y * width + x;
            if (binary_data[idx] > 0) {
                sum++;
            }
        }
        vertical_projection[y] = (float)sum;
    }

    float threshold = (float)width * 0.3f;

    int in_line = 0;
    int line_start = 0;
    int line_end = 0;

    for (int y = 0; y < height; y++) {
        if (vertical_projection[y] > threshold) {
            if (!in_line) {
                line_start = y;
                in_line = 1;
            }
        } else {
            if (in_line) {
                line_end = y;
                *out_position = (line_start + line_end) / 2;
                free(vertical_projection);
                return SUCCESS;
            }
        }
    }

    if (in_line) {
        *out_position = line_start;
        free(vertical_projection);
        return SUCCESS;
    }

    free(vertical_projection);
    return FAIL;
}

int detect_vertical_line(
    const uint8_t* binary_data,
    int width,
    int height,
    int* out_position
) {
    if (binary_data == NULL || width <= 0 || height <= 0 || out_position == NULL) {
        return FAIL;
    }

    float* horizontal_projection = (float*)malloc(width * sizeof(float));
    if (horizontal_projection == NULL) {
        return FAIL;
    }

    for (int x = 0; x < width; x++) {
        int sum = 0;
        for (int y = 0; y < height; y++) {
            int idx = y * width + x;
            if (binary_data[idx] > 0) {
                sum++;
            }
        }
        horizontal_projection[x] = (float)sum / 255.0f;
    }

    float threshold = height * 0.3f;

    int in_line = 0;
    int line_start = 0;
    int line_end = 0;

    for (int x = 0; x < width; x++) {
        if (horizontal_projection[x] > threshold) {
            if (!in_line) {
                line_start = x;
                in_line = 1;
            }
        } else {
            if (in_line) {
                line_end = x;
                *out_position = (line_start + line_end) / 2;
                free(horizontal_projection);
                return SUCCESS;
            }
        }
    }

    if (in_line) {
        *out_position = line_start;
        free(horizontal_projection);
        return SUCCESS;
    }

    free(horizontal_projection);
    return FAIL;
}

int calculate_confidence(
    const uint8_t* binary_data,
    const uint8_t* gray_data,
    int line_pos,
    int dimension,
    int axis
) {
    if (binary_data == NULL || gray_data == NULL) {
        return 50;
    }

    int width = dimension;
    int height = dimension;

    int start = line_pos - 5;
    int end = line_pos + 5;

    if (start < 0) start = 0;
    if (end > dimension) end = dimension;

    int region_size = 0;
    int black_count = 0;
    int gray_sum = 0;

    if (axis == 'y' || axis == 'Y' || axis == 1) {
        for (int y = start; y < end && y < height; y++) {
            for (int x = 0; x < width; x++) {
                int idx = y * width + x;
                region_size++;
                if (binary_data[idx] > 0) {
                    black_count++;
                }
                gray_sum += gray_data[idx];
            }
        }
    } else {
        for (int y = 0; y < height; y++) {
            for (int x = start; x < end && x < width; x++) {
                int idx = y * width + x;
                region_size++;
                if (binary_data[idx] > 0) {
                    black_count++;
                }
                gray_sum += gray_data[idx];
            }
        }
    }

    if (region_size == 0) {
        return 50;
    }

    float black_density = (float)black_count / (float)region_size;
    float gray_value = (float)gray_sum / (float)region_size;
    float contrast = (255.0f - gray_value) / 255.0f;
    float continuity = black_density;

    int confidence = (int)(black_density * 40.0f + contrast * 30.0f + continuity * 30.0f);
    if (confidence > 100) confidence = 100;
    if (confidence < 10) confidence = 10;

    return confidence;
}
