#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'tools/extract-utils'))

from extract_utils.file import File
from extract_utils.fixups_blob import (
    BlobFixupCtx,
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.fixups_lib import (
    lib_fixups,
    lib_fixups_user_type,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)


def fixup_agm_without_ats(ctx, file, file_path, *args, **kwargs):
    # Sheng has no ATS diagnostic socket. Do not start its 120-retry worker.
    # Keep the real session_obj_init call and its original error return path.
    from pathlib import Path
    from hashlib import sha256
    p = Path(file_path)
    data = bytearray(p.read_bytes())
    before = "5e03733144c4f9675c4bc7cd49dfd93f420896f53671215b58234a91a8547ac8"
    after = "88748c9c8e067e9278d084daac1fd98a5eab5807107cba2686b61022927424c0"
    digest = sha256(data).hexdigest()
    if digest == after:
        return
    if digest != before:
        raise ValueError("Unexpected Sheng libagm build; review ATS entry points")
    for offset, old, new in [(0x11f94, "e00000d0", "07000014"),
                             (0x11fb8, "80010034", "0c000014")]:
        assert data[offset:offset + 4] == bytes.fromhex(old)
        data[offset:offset + 4] = bytes.fromhex(new)
    assert sha256(data).hexdigest() == after
    p.write_bytes(data)

namespace_imports = [
    'device/xiaomi/sm8550-sheng-common',
    'hardware/xiaomi',
    'vendor/qcom/common/system/telephony',
]

def lib_fixup_vendor_suffix(lib: str, partition: str, *args, **kwargs):
    return f'{lib}-{partition}' if partition == 'vendor' else None


def lib_fixup_audio_primary(lib: str, partition: str, *args, **kwargs):
    return f'{lib}_sheng'

lib_fixups: lib_fixups_user_type = {
    **lib_fixups,
    'audio.primary.kalama': lib_fixup_audio_primary,
    (
        'vendor.display.color@1.0',
        'vendor.display.color@1.1',
        'vendor.display.color@1.2',
        'vendor.display.color@1.3',
        'vendor.display.postproc@1.0',
        'vendor.qti.hardware.limits@1.0',
        'vendor.qti.hardware.limits@1.1',
        'vendor.qti.hardware.qccsyshal@1.0',
        'vendor.qti.hardware.qccsyshal@1.1',
        'vendor.qti.hardware.qccsyshal@1.2',
        'vendor.qti.hardware.qccvndhal@1.0',
        'vendor.qti.hardware.wifidisplaysession@1.0',
        'vendor.qti.imsrtpservice@3.0',
        'vendor.qti.imsrtpservice@3.1',
        'vendor.qti.diaghal@1.0',
    ): lib_fixup_vendor_suffix,
}

blob_fixups: blob_fixups_user_type = {
    'vendor/lib64/libagm.so': blob_fixup().call(fixup_agm_without_ats, need_tmp_dir=False),
    'system_ext/lib64/libwfdservice.so': blob_fixup()
        .replace_needed('android.media.audio.common.types-V4-cpp.so', 'android.media.audio.common.types-V5-cpp.so'),
    'system_ext/lib64/vendor.qti.hardware.qccsyshal@1.2-halimpl.so': blob_fixup()
        .replace_needed('libprotobuf-cpp-full.so', 'libprotobuf-cpp-full-21.7.so'),
    'odm/lib64/libmt@1.3.so': blob_fixup()
        .replace_needed('libcrypto.so', 'libcrypto-v33.so'),
    (
        'vendor/bin/hw/android.hardware.security.keymint-service-qti',
        'vendor/lib64/libqtikeymint.so'
    ): blob_fixup()
        .add_needed('android.hardware.security.rkp-V3-ndk.so'),
    'vendor/etc/public.libraries.txt': blob_fixup()
        .regex_replace('libqti-perfd-client.so\n', ''),
    'vendor/etc/seccomp_policy/qwesd@2.0.policy': blob_fixup()
        .add_line_if_missing('pipe2: 1'),
    'vendor/lib64/libqcodec2_core.so': blob_fixup()
        .add_needed('libcodec2_shim.so'),
    'vendor/lib64/vendor.libdpmframework.so': blob_fixup()
        .add_needed('libhidlbase_shim.so'),
    (
        'vendor/bin/hw/android.hardware.contexthub-service.qmi',
        'vendor/lib64/libstfactory-vendor.so',
        'odm/lib64/nfc_nci.nqx.default.hw.so'
    ): blob_fixup()
        .add_needed('libbase_shim.so'),
    'vendor/etc/media_codecs_kalama.xml': blob_fixup()
        .regex_replace(r'\s*<MediaCodec\b[^>]*name=\"c2\.dolby\.[^>]*>[\s\S]*?<\/MediaCodec>', '')
        .regex_replace('.+media_codecs_(dolby_audio|google_audio|google_c2|google_telephony|vendor_audio).+\n', ''),
    'vendor/etc/vintf/manifest/c2_manifest_vendor.xml': blob_fixup()
        .regex_replace(r'\s*<fqname>@1\.0::IComponentStore/dolby</fqname>', '')
        .regex_replace('.+DOLBY.+\n', ''),
    (
        'vendor/lib64/libdpps.so',
        'vendor/lib64/libsnapdragoncolor-manager.so'
    ): blob_fixup()
        .replace_needed('libtinyxml2.so', 'libtinyxml2-v34.so'),
    'vendor/etc/init/hw/init.batterysecret.rc': blob_fixup()
        .regex_replace('group system system wakelock', 'group system system usb wakelock'),
}  # fmt: skip

module = ExtractUtilsModule(
    'sm8550-sheng-common',
    'xiaomi',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=namespace_imports,
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
