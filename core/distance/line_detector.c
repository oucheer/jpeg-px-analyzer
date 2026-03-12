#include "line_detector.h"
#include <string.h>

static const uint8_t gaussian_kernel_3x3[3][3] = {
    {1, 2, 1},
    {2, 4, 2},
    {1, 2, 1}
};

int gaussian_blur_uint8(const uint8_t* input, uint8_t* output, int width, int height) {
    if (input == NULL || output == NULL || width <= 0 || height <= 0) {
        return FAIL;
    }

    uint8_t* temp = (uint8_t*)malloc(width * height * sizeof(uint8_t));
    if (temp == NULL) {
        return FAIL;
    }

    memcpy(temp, input, width * height * sizeof(uint8_t));

    for (int y = 1; y < height - 1; y++) {
        for (int x = 1; x < width - 1; x++) {
            int sum = 0;
            int kernel_sum = 0;

            for (int ky = -1; ky <= 1; ky++) {
                for (int kx = -1; kx <= 1; kx++) {
                    int px = x + kx;
                    int py = y + ky;
                    uint8_t val = temp[py * width + px];
                    int weight = gaussian_kernel_3x3[ky + 1][kx + 1];
                    sum += val * weight;
                    kernel_sum += weight;
                }
            }

            output[y * width + x] = (uint8_t)(sum / kernel_sum);
        }
    }

    output[0] = input[0];
    output[width - 1] = input[width - 1];
    output[(height - 1) * width] = input[(height - 1) * width];
    output[height * width - 1] = input[height * width - 1];

    for (int x = 1; x < width - 1; x++) {
        output[x] = input[x];
        output[(height - 1) * width + x] = input[(height - 1) * width + x];
    }

    for (int y = 1; y < height - 1; y++) {
        output[y * width] = input[y * width];
        output[y * width + width - 1] = input[y * width + width - 1];
    }

    free(temp);
    return SUCCESS;
}

int sobel_edge_detection(const uint8_t* input, uint8_t* output, int width, int height) {
    if (input == NULL || output == NULL || width <= 0 || height <= 0) {
        return FAIL;
    }

    int sobel_x[3][3] = {
        {-1, 0, 1},
        {-2, 0, 2},
        {-1, 0, 1}
    };

    int sobel_y[3][3] = {
        {-1, -2, -1},
        {0, 0, 0},
        {1, 2, 1}
    };

    uint8_t* blurred = (uint8_t*)malloc(width * height * sizeof(uint8_t));
    if (blurred == NULL) {
        return FAIL;
    }

    gaussian_blur_uint8(input, blurred, width, height);

    for (int y = 1; y < height - 1; y++) {
        for (int x = 1; x < width - 1; x++) {
            int gx = 0;
            int gy = 0;

            for (int ky = -1; ky <= 1; ky++) {
                for (int kx = -1; kx <= 1; kx++) {
                    uint8_t val = blurred[(y + ky) * width + (x + kx)];
                    gx += val * sobel_x[ky + 1][kx + 1];
                    gy += val * sobel_y[ky + 1][kx + 1];
                }
            }

            int magnitude = (int)sqrtf((float)(gx * gx + gy * gy));
            if (magnitude > 255) magnitude = 255;

            output[y * width + x] = (uint8_t)magnitude;
        }
    }

    memset(output, 0, width);
    memset(output + (height - 1) * width, 0, width);
    for (int y = 0; y < height; y++) {
        output[y * width] = 0;
        output[y * width + width - 1] = 0;
    }

    free(blurred);
    return SUCCESS;
}

int compute_vertical_projection(const uint8_t* edge_data, float* projection, int width, int height) {
    if (edge_data == NULL || projection == NULL || width <= 0 || height <= 0) {
        return FAIL;
    }

    for (int x = 0; x < width; x++) {
        float sum = 0.0f;
        for (int y = 0; y < height; y++) {
            sum += (float)edge_data[y * width + x];
        }
        projection[x] = sum;
    }

    return SUCCESS;
}

int compute_horizontal_projection(const uint8_t* edge_data, float* projection, int width, int height) {
    if (edge_data == NULL || projection == NULL || width <= 0 || height <= 0) {
        return FAIL;
    }

    for (int y = 0; y < height; y++) {
        float sum = 0.0f;
        for (int x = 0; x < width; x++) {
            sum += (float)edge_data[y * width + x];
        }
        projection[y] = sum;
    }

    return SUCCESS;
}

int find_peaks_simple(const float* projection, int length, int* peaks, int max_peaks, float threshold_ratio) {
    if (projection == NULL || peaks == NULL || length <= 0 || max_peaks <= 0) {
        return 0;
    }

    float max_val = 0.0f;
    for (int i = 0; i < length; i++) {
        if (projection[i] > max_val) {
            max_val = projection[i];
        }
    }

    if (max_val == 0.0f) {
        return 0;
    }

    float threshold = max_val * threshold_ratio;
    int peak_count = 0;

    for (int i = 2; i < length - 2 && peak_count < max_peaks; i++) {
        if (projection[i] > threshold) {
            if (projection[i] >= projection[i-1] && 
                projection[i] >= projection[i-2] &&
                projection[i] >= projection[i+1] && 
                projection[i] >= projection[i+2]) {
                peaks[peak_count++] = i;
            }
        }
    }

    return peak_count;
}

int find_peaks_weighted(const float* projection, int length, int* raw_peaks, float* weighted_peaks, int max_peaks, float threshold_ratio) {
    if (projection == NULL || raw_peaks == NULL || weighted_peaks == NULL) {
        return 0;
    }

    int num_peaks = find_peaks_simple(projection, length, raw_peaks, max_peaks, threshold_ratio);

    for (int i = 0; i < num_peaks; i++) {
        int peak_idx = raw_peaks[i];
        
        int start = peak_idx - 5;
        int end = peak_idx + 6;
        if (start < 0) start = 0;
        if (end > length) end = length;

        float total_weight = 0.0f;
        float weighted_sum = 0.0f;

        for (int j = start; j < end; j++) {
            float weight = projection[j];
            weighted_sum += (float)j * weight;
            total_weight += weight;
        }

        if (total_weight > 0.0f) {
            weighted_peaks[i] = weighted_sum / total_weight;
        } else {
            weighted_peaks[i] = (float)peak_idx;
        }
    }

    return num_peaks;
}

int analyze_dark_regions(const uint8_t* gray_data, int width, int height, int* dark_col, int* dark_row, int edge_margin) {
    if (gray_data == NULL || width <= 0 || height <= 0) {
        return FAIL;
    }

    float* row_means = (float*)malloc(height * sizeof(float));
    float* col_means = (float*)malloc(width * sizeof(float));
    if (row_means == NULL || col_means == NULL) {
        free(row_means);
        free(col_means);
        return FAIL;
    }

    for (int y = 0; y < height; y++) {
        float sum = 0.0f;
        for (int x = 0; x < width; x++) {
            sum += (float)gray_data[y * width + x];
        }
        row_means[y] = sum / (float)width;
    }

    for (int x = 0; x < width; x++) {
        float sum = 0.0f;
        for (int y = 0; y < height; y++) {
            sum += (float)gray_data[y * width + x];
        }
        col_means[x] = sum / (float)height;
    }

    int bg_row_region = (height > 50) ? 50 : height;
    float bg_row = 0.0f;
    for (int y = height - bg_row_region; y < height; y++) {
        bg_row += row_means[y];
    }
    bg_row /= (float)bg_row_region;

    int bg_col_region = (width > 50) ? 50 : width;
    float bg_col = 0.0f;
    for (int x = width - bg_col_region; x < width; x++) {
        bg_col += col_means[x];
    }
    bg_col /= (float)bg_col_region;

    float row_threshold = bg_row * 0.85f;
    float col_threshold = bg_col * 0.85f;

    if (dark_col != NULL) {
        *dark_col = -1;
        for (int x = edge_margin; x < width; x++) {
            if (col_means[x] < col_threshold) {
                *dark_col = x;
                break;
            }
        }
    }

    if (dark_row != NULL) {
        *dark_row = -1;
        for (int y = edge_margin; y < height; y++) {
            if (row_means[y] < row_threshold) {
                *dark_row = y;
                break;
            }
        }
    }

    free(row_means);
    free(col_means);
    return SUCCESS;
}

int compute_median(int* values, int count) {
    if (values == NULL || count <= 0) {
        return 0;
    }

    if (count == 1) {
        return values[0];
    }

    int* sorted = (int*)malloc(count * sizeof(int));
    if (sorted == NULL) {
        return values[0];
    }

    memcpy(sorted, values, count * sizeof(int));

    for (int i = 0; i < count - 1; i++) {
        for (int j = i + 1; j < count; j++) {
            if (sorted[i] > sorted[j]) {
                int temp = sorted[i];
                sorted[i] = sorted[j];
                sorted[j] = temp;
            }
        }
    }

    int median = sorted[count / 2];
    free(sorted);
    return median;
}

int filter_outliers_iqr(int* values, int count, int* filtered, int max_filtered) {
    if (values == NULL || filtered == NULL || count <= 0) {
        return 0;
    }

    if (count < 4) {
        int copy_count = (count < max_filtered) ? count : max_filtered;
        memcpy(filtered, values, copy_count * sizeof(int));
        return copy_count;
    }

    int sorted[MAX_CANDIDATES];
    memcpy(sorted, values, count * sizeof(int));

    for (int i = 0; i < count - 1; i++) {
        for (int j = i + 1; j < count; j++) {
            if (sorted[i] > sorted[j]) {
                int temp = sorted[i];
                sorted[i] = sorted[j];
                sorted[j] = temp;
            }
        }
    }

    int q1 = sorted[count / 4];
    int q3 = sorted[count * 3 / 4];
    int iqr = q3 - q1;

    int filtered_count = 0;
    if (iqr > 0) {
        for (int i = 0; i < count && filtered_count < max_filtered; i++) {
            if (values[i] >= q1 - iqr && values[i] <= q3 + iqr) {
                filtered[filtered_count++] = values[i];
            }
        }
    }

    if (filtered_count == 0) {
        filtered_count = (count < max_filtered) ? count : max_filtered;
        memcpy(filtered, values, filtered_count * sizeof(int));
    }

    return filtered_count;
}

int detect_lines_multi_strategy(
    const uint8_t* gray_data,
    int width,
    int height,
    int edge_margin,
    int* out_vertical_px,
    int* out_horizontal_px
) {
    if (gray_data == NULL || width <= 0 || height <= 0 || out_vertical_px == NULL || out_horizontal_px == NULL) {
        return FAIL;
    }

    int x_candidates[MAX_CANDIDATES];
    int y_candidates[MAX_CANDIDATES];
    int x_count = 0;
    int y_count = 0;

    int search_configs[4][2] = {
        {width / 4, height / 4},
        {width / 3, height / 3},
        {(width / 3 < 400) ? width / 3 : 400, (height / 3 < 400) ? height / 3 : 400},
        {(width / 3 < 500) ? width / 3 : 500, (height / 3 < 500) ? height / 3 : 500}
    };

    for (int cfg = 0; cfg < 4 && x_count < MAX_CANDIDATES && y_count < MAX_CANDIDATES; cfg++) {
        int roi_w = search_configs[cfg][0];
        int roi_h = search_configs[cfg][1];

        uint8_t* blurred = (uint8_t*)malloc(roi_w * roi_h * sizeof(uint8_t));
        uint8_t* edges = (uint8_t*)malloc(roi_w * roi_h * sizeof(uint8_t));
        float* v_proj = (float*)malloc(roi_w * sizeof(float));
        float* h_proj = (float*)malloc(roi_h * sizeof(float));

        if (blurred == NULL || edges == NULL || v_proj == NULL || h_proj == NULL) {
            free(blurred);
            free(edges);
            free(v_proj);
            free(h_proj);
            continue;
        }

        for (int y = 0; y < roi_h; y++) {
            for (int x = 0; x < roi_w; x++) {
                blurred[y * roi_w + x] = gray_data[y * width + x];
            }
        }

        gaussian_blur_uint8(blurred, blurred, roi_w, roi_h);
        sobel_edge_detection(blurred, edges, roi_w, roi_h);
        compute_vertical_projection(edges, v_proj, roi_w, roi_h);
        compute_horizontal_projection(edges, h_proj, roi_w, roi_h);

        int raw_peaks[32];
        float weighted_peaks[32];

        int num_v_peaks = find_peaks_weighted(v_proj, roi_w, raw_peaks, weighted_peaks, 32, 0.10f);
        for (int i = 0; i < num_v_peaks && x_count < MAX_CANDIDATES; i++) {
            int pos = (int)(weighted_peaks[i] + 0.5f);
            if (pos > edge_margin) {
                x_candidates[x_count++] = pos;
            }
        }

        int num_h_peaks = find_peaks_weighted(h_proj, roi_h, raw_peaks, weighted_peaks, 32, 0.10f);
        for (int i = 0; i < num_h_peaks && y_count < MAX_CANDIDATES; i++) {
            int pos = (int)(weighted_peaks[i] + 0.5f);
            if (pos > edge_margin) {
                y_candidates[y_count++] = pos;
            }
        }

        int dark_col = -1, dark_row = -1;
        analyze_dark_regions(gray_data, roi_w, roi_h, &dark_col, &dark_row, edge_margin);
        if (dark_col > edge_margin && x_count < MAX_CANDIDATES) {
            x_candidates[x_count++] = dark_col;
        }
        if (dark_row > edge_margin && y_count < MAX_CANDIDATES) {
            y_candidates[y_count++] = dark_row;
        }

        free(blurred);
        free(edges);
        free(v_proj);
        free(h_proj);
    }

    int corner_configs[4][4] = {
        {0, 0, width / 4, height / 4},
        {width / 8, 0, width / 4, height / 4},
        {0, height / 8, width / 4, height / 4},
        {width / 10, height / 10, width / 5, height / 5}
    };

    for (int cfg = 0; cfg < 4 && x_count < MAX_CANDIDATES && y_count < MAX_CANDIDATES; cfg++) {
        int x_off = corner_configs[cfg][0];
        int y_off = corner_configs[cfg][1];
        int roi_w = corner_configs[cfg][2];
        int roi_h = corner_configs[cfg][3];

        if (x_off + roi_w > width || y_off + roi_h > height) {
            continue;
        }

        int dark_col = -1, dark_row = -1;
        analyze_dark_regions(gray_data + y_off * width + x_off, roi_w, roi_h, &dark_col, &dark_row, edge_margin);

        if (dark_col > 0 && x_count < MAX_CANDIDATES) {
            x_candidates[x_count++] = dark_col + x_off;
        }
        if (dark_row > 0 && y_count < MAX_CANDIDATES) {
            y_candidates[y_count++] = dark_row + y_off;
        }
    }

    if (x_count > 0) {
        int valid_x[MAX_CANDIDATES];
        int valid_count = 0;
        for (int i = 0; i < x_count; i++) {
            if (x_candidates[i] > edge_margin) {
                valid_x[valid_count++] = x_candidates[i];
            }
        }

        if (valid_count > 0) {
            *out_vertical_px = valid_x[0];
        } else {
            *out_vertical_px = 0;
        }
    } else {
        *out_vertical_px = 0;
    }

    if (y_count > 0) {
        int valid_y[MAX_CANDIDATES];
        int valid_count = 0;
        for (int i = 0; i < y_count; i++) {
            if (y_candidates[i] > edge_margin) {
                valid_y[valid_count++] = y_candidates[i];
            }
        }

        if (valid_count > 0) {
            *out_horizontal_px = valid_y[0];
        } else {
            *out_horizontal_px = 0;
        }
    } else {
        *out_horizontal_px = 0;
    }

    if (*out_vertical_px > 0 && *out_horizontal_px > 0) {
        return SUCCESS;
    }

    return FAIL;
}

float pixels_to_mm(int pixels, int dpi) {
    if (dpi <= 0) {
        dpi = 600;
    }
    float result = pixels * 25.4f / (float)dpi;
    result = roundf(result * 100.0f) / 100.0f;
    return result;
}
