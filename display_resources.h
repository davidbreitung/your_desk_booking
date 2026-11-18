#pragma once
#include <cmath>
#include <cstdint>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_heap_caps.h"
#include "esp_ota_ops.h"
#include "esp_image_format.h"

namespace desk_resources {
// Delta of both idle task counters: normalized across both CPU cores.
// Unsigned subtraction also handles the 32-bit runtime-clock rollover.
inline float cpu_busy() {
  static TaskStatus_t tasks[64];
  static uint32_t previous_total = 0, previous_idle[portNUM_PROCESSORS] = {};
  static bool ready = false;
  uint32_t total = 0, idle[portNUM_PROCESSORS] = {};
  bool found[portNUM_PROCESSORS] = {};
  const auto count = uxTaskGetSystemState(tasks, 64, &total);
  if (!count) { ready = false; return NAN; }
  for (int core = 0; core < portNUM_PROCESSORS; ++core) {
    auto handle = xTaskGetIdleTaskHandleForCPU(core);
    for (unsigned i = 0; i < count; ++i) {
      if (tasks[i].xHandle == handle) { idle[core] = tasks[i].ulRunTimeCounter; found[core] = true; break; }
    }
    if (!found[core]) { ready = false; return NAN; }
  }
  const uint32_t elapsed = total - previous_total;
  uint64_t idle_elapsed = 0;
  for (int core = 0; core < portNUM_PROCESSORS; ++core) {
    idle_elapsed += uint32_t(idle[core] - previous_idle[core]);
    previous_idle[core] = idle[core];
  }
  previous_total = total;
  if (!ready || !elapsed) { ready = true; return NAN; }
  float busy = 100.0f * (1.0 - double(idle_elapsed) / (double(elapsed) * portNUM_PROCESSORS));
  return std::fmax(0.0f, std::fmin(100.0f, busy));
}

inline float used_percent(uint32_t capabilities) {
  const auto total = heap_caps_get_total_size(capabilities);
  return total ? 100.0f * (1.0f - float(heap_caps_get_free_size(capabilities)) / total) : NAN;
}

inline float firmware_percent() {
  static float result = NAN;
  static bool measured = false;
  if (!measured) {
    measured = true;
    const esp_partition_t *partition = esp_ota_get_running_partition();
    if (!partition) return NAN;
    esp_partition_pos_t position = {partition->address, partition->size};
    esp_image_metadata_t metadata = {};
    if (esp_image_verify(ESP_IMAGE_VERIFY_SILENT, &position, &metadata) == ESP_OK)
      result = 100.0f * metadata.image_len / partition->size;
  }
  return result;
}
}
