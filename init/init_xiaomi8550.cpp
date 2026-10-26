/*
   Copyright (c) 2015, The Linux Foundation. All rights reserved.
                 2016 The CyanogenMod Project.
                 2019-2020 The LineageOS Project.
                 2021 The Android Open Source Project.
                 2022-2024 Paranoid Android.

   SPDX-License-Identifier: Apache-2.0

 */

#include <cstdlib>
#include <string.h>
#include <unistd.h>

#define _REALLY_INCLUDE_SYS__SYSTEM_PROPERTIES_H_
#include <sys/_system_properties.h>
#include <android-base/properties.h>

#include "property_service.h"
#include "vendor_init.h"

using android::base::GetProperty;
using std::string;

// List of partitions to override props
static const string source_partitions[] = {
    "", "bootimage.", "odm.", "product.", "system.",
    "system_dlkm.", "system_ext.", "vendor.", "vendor_dlkm."
};

bool IsRecoveryMode() {
    return access("/system/bin/recovery", F_OK) == 0;
}

void property_override(char const prop[], char const value[]) {
    auto pi = (prop_info*) __system_property_find(prop);

    if (pi != nullptr)
        __system_property_update(pi, value, strlen(value));
    else
        __system_property_add(prop, strlen(prop), value, strlen(value));
}

void set_build_prop(const string &prop, const string &value) {
    property_override(prop.c_str(), value.c_str());
}

void set_ro_build_prop(const string &prop, const string &value) {
    string prop_name;
    for (const string &source : source_partitions) {
        prop_name = "ro.product." + source + prop;
        property_override(prop_name.c_str(), value.c_str());
    }
}

void vendor_load_properties() {
    // This library is built only for Sheng. Never adopt an arbitrary boot SKU.
    const string region = GetProperty("ro.boot.hwc", "");
    const bool china = region == "CN";
    set_build_prop("ro.build.product", "sheng");
    set_ro_build_prop("device", "sheng");
    set_ro_build_prop("model", china ? "24018RPACC" : "24018RPACG");
    set_ro_build_prop("name", china ? "sheng" : "sheng_global");
    set_build_prop("ro.product.mod_device", china ? "sheng" : "sheng_global");
}
