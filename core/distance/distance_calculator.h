#ifndef DISTANCE_CALCULATOR_H
#define DISTANCE_CALCULATOR_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define SUCCESS 1
#define FAIL 0

float pixels_to_mm(int pixels, int dpi);

int detect_horizontal_line(
    const uint8_t* binary_data,
    int width,
    int height,
    int* out_position
);

int detect_vertical_line(
    const uint8_t* binary_data,
    int width,
    int height,
    int* out_position
);

int calculate_confidence(
    const uint8_t* binary_data,
    const uint8_t* gray_data,
    int line_pos,
    int dimension,
    int axis
);

#ifdef __cplusplus
}
#endif

#endif
