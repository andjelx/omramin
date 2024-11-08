import typing as T

from dataclasses import dataclass
import enum
import logging
import logging.config

import httpx
import utils as U


########################################################################################################################

L = logging.getLogger("omron")

_OMRON_APP_ID = "lou30y2xfa9f"
_OMRON_API_KEY = "392a4bdff8af4141944d30ca8e3cc860"

_OGSC_APP_VERSION = "010.003.00001"
_OGSC_SDK_VERSION = "000.101"

_USER_AGENT = f"OmronConnect/{_OGSC_APP_VERSION}.001 CFNetwork/1335.0.3.4 Darwin/21.6.0)"

_debugSaveResponse = False

########################################################################################################################
# 8195 -> kg
# 8208 -> lb
# 8224 -> st
# 24577 -> mg/dL
# 24593 -> mmol/L
# 4099 -> km
# 4112 -> mile
# 20483 -> kPa
# 20496 -> mmHg
# 61536 -> steps
# 61584 -> percentage
# 61600 -> bpm
# 16387 -> kcal
# 12288 -> °C
# 12304 -> °F

# 4098 -> cm
# 4113 -> inch
# 8192 -> g


class Gender(enum.IntEnum):
    MALE = 1
    FEMALE = 2


class LengthUnit(enum.IntEnum):
    CM = 4098
    INCH = 4113
    KM = 4099
    MILE = 4112


class WeightUnit(enum.IntEnum):
    G = 8192
    KG = 8195
    LB = 8208
    ST = 8224


class ValueType(enum.StrEnum):
    MMHG_MAX_FIGURE = "1"  # ("%1$,3.0f", 1, 20496, R.string.msg0000808, R.string.msg0020959),
    KPA_MAX_FIGURE = "1"  # ("%.1f", 1, 20483, R.string.msg0000809, R.string.msg0020993),
    MMHG_MIN_FIGURE = "2"  # ("%1$,3.0f", 2, 20496, R.string.msg0000808, R.string.msg0020959),
    KPA_MIN_FIGURE = "2"  # ("%.1f", 2, 20483, R.string.msg0000809, R.string.msg0020993),
    BPM_FIGURE = "3"  # ("%1$,3.0f", 3, 61600, R.string.msg0000815, R.string.msg0020960),
    ATTITUDE_FIGURE = "4"  # ("%.0f", 4, -1, -1, -1),
    ROOM_TEMPERATURE_FIGURE = "5"  # ("%.0f", 5, -1, R.string.msg0000823, R.string.msg0020972),
    ARRHYTHMIA_FLAG_FIGURE = "6"  # ("%.0f", 6, -1, -1, -1),
    BODY_MOTION_FLAG_FIGURE = "7"  # ("%.0f", 7, -1, -1, -1),
    POSTURE_GUIDE = "20"  # ("%.0f", 20, -1, -1, -1),
    KEEP_UP_CHECK_FIGURE = "8"  # ("%.0f", 8, -1, -1, -1),
    PULSE_QUIET_CHECK_FIGURE = "9"  # ("%.0f", 9, -1, -1, -1),
    CONTINUOUS_MEASUREMENT_COUNT_FIGURE = "10"  # ("%1$,3.0f", 10, -1, R.string.msg0000821, R.string.msg0000821),
    ARTIFACT_COUNT_FIGURE = "11"  # ("%1$,3.0f", 11, -1, R.string.msg0000821, R.string.msg0000821),
    IRREGULAR_PULSE_COUNT_FIGURE = "37"  # ("%1$,3.0f", 37, -1, R.string.msg0020505, R.string.msg0020505),
    MEASUREMENT_MODE_FIGURE = "38"  # ("%.0f", 38, -1, -1, -1),
    NOCTURNAL_ERROR_CODE_FIGURE = "41"  # ("%.0f", 41, -1, -1, -1),
    NNOCTURNAL_ERROR_CODE_DISPLAY_FIGURE = "45"  # ("%.0f", 45, -1, -1, -1),
    KG_FIGURE = "257"  # ("%.2f", 257, 8195, R.string.msg0000803, R.string.msg0020986),
    KG_SKELETAL_MUSCLE_MASS_FIGURE = "294"  # ("%.1f", 294, 8195, R.string.msg0000803, R.string.msg0020986),
    KG_BODY_FAT_MASS_FIGURE = "295"  # ("%.1f", 295, 8195, R.string.msg0000803, R.string.msg0020986),
    LB_FIGURE = "257"  # ("%.1f", 257, 8208, R.string.msg0000804, R.string.msg0020994),
    ST_FIGURE = "257"  # ("%.0f", 257, 8224, R.string.msg0000805, R.string.msg0020995),
    BODY_FAT_PER_FIGURE = "259"  # ("%.1f", 259, 61584, R.string.msg0000817, R.string.msg0000817),
    VISCERAL_FAT_FIGURE = "264"  # ("%1$,3.0f", 264, -1, R.string.msg0000816, R.string.msg0020987),
    VISCERAL_FAT_FIGURE_702T = "264"  # ("%1$,3.1f", 264, -1, R.string.msg0000816, R.string.msg0020987),
    RATE_SKELETAL_MUSCLE_FIGURE = "261"  # ("%.1f", 261, 61584, R.string.msg0000817, R.string.msg0000817),
    RATE_SKELETAL_MUSCLE_BOTH_ARMS_FIGURE = "275"  # ("%.1f", 275, 61584, R.string.msg0000817, R.string.msg0000817),
    RATE_SKELETAL_MUSCLE_BODY_TRUNK_FIGURE = "277"  # ("%.1f", 277, 61584, R.string.msg0000817, R.string.msg0000817),
    RATE_SKELETAL_MUSCLE_BOTH_LEGS_FIGURE = "279"  # ("%.1f", 279, 61584, R.string.msg0000817, R.string.msg0000817),
    RATE_SUBCUTANEOUS_FAT_FIGURE = "281"  # ("%.1f", 281, 61584, R.string.msg0000817, R.string.msg0000817),
    RATE_SUBCUTANEOUS_FAT_BOTH_ARMS_FIGURE = "283"  # ("%.1f", 283, 61584, R.string.msg0000817, R.string.msg0000817),
    RATE_SUBCUTANEOUS_FAT_BODY_TRUNK_FIGURE = "285"  # ("%.1f", 285, 61584, R.string.msg0000817, R.string.msg0000817),
    RATE_SUBCUTANEOUS_FAT_BOTH_LEGS_FIGURE = "287"  # ("%.1f", 287, 61584, R.string.msg0000817, R.string.msg0000817),
    BIOLOGICAL_AGE_FIGURE = "263"  # ("%1$,3.0f", 263, 61568, R.string.msg0000822, R.string.msg0020989),
    BASAL_METABOLISM_FIGURE = "260"  # ("%1$,3.0f", 260, 16387, R.string.msg0000824, R.string.msg0020988),
    BMI_FIGURE = "262"  # ("%.1f", 262, -1, -1, -1),
    BLE_BMI_FIGURE = "292"  # ("%.1f", 292, -1, -1, -1),
    VISCERAL_FAT_CHECK_FIGURE = "265"  # ("%.0f", 265, -1, -1, -1),
    RATE_SKELETAL_MUSCLE_CHECK_FIGURE = "266"  # ("%.0f", 266, -1, -1, -1),
    RATE_SKELETAL_MUSCLE_BOTH_ARMS_CHECK_FIGURE = "276"  # ("%.0f", 276, -1, -1, -1),
    RATE_SKELETAL_MUSCLE_BODY_TRUNK_CHECK_FIGURE = "278"  # ("%.0f", 278, -1, -1, -1),
    RATE_SKELETAL_MUSCLE_BOTH_LEGS_CHECK_FIGURE = "280"  # ("%.0f", 280, -1, -1, -1),
    RATE_SUBCUTANEOUS_FAT_CHECK_FIGURE = "282"  # ("%.0f", 282, -1, -1, -1),
    RATE_SUBCUTANEOUS_FAT_BOTH_ARMS_CHECK_FIGURE = "284"  # ("%.0f", 284, -1, -1, -1),
    RATE_SUBCUTANEOUS_FAT_BODY_TRUNK_CHECK_FIGURE = "286"  # ("%.0f", 286, -1, -1, -1),
    RATE_SUBCUTANEOUS_FAT_BOTH_LEGS_CHECK_FIGURE = "288"  # ("%.0f", 288, -1, -1, -1),
    IMPEDANCE_FIGURE = "267"  # ("%.0f", 267, -1, -1, -1),
    WEIGHT_FFM_FIGURE = "268"  # ("%.0f", 268, -1, -1, -1),
    AVERAGE_WEIGHT_FIGURE = "269"  # ("%.0f", 269, -1, -1, -1),
    AVERAGE_WEIGHT_FFM_FIGURE = "270"  # ("%.0f", 270, -1, -1, -1),
    MMOLL_FIGURE = "2305"  # ("%.1f", 2305, 24593, R.string.msg0000811, R.string.msg0020975),
    MGDL_FIGURE = "2305"  # ("%.0f", 2305, 24577, R.string.msg0000810, R.string.msg0020976),
    MEAL_FIGURE = "2306"  # ("%.0f", 2306, -1, -1, -1),
    TYPE_FIGURE = "2307"  # ("%.0f", 2307, -1, -1, -1),
    SAMPLE_LOCATION_FIGURE = "2308"  # ("%.0f", 2308, -1, -1, -1),
    HIGH_LOW_DETECTION_FIGURE = "2309"  # ("%.0f", 2309, -1, -1, -1),
    STEPS_FIGURE = "513"  # ("%1$,3.0f", 513, 61536, R.string.msg0000833, R.string.msg0020991),
    TIGHTLY_STEPS = "514"  # ("%1$,3.0f", 514, 61536, R.string.msg0000833, R.string.msg0020991),
    STAIR_UP_STEPS = "518"  # ("%1$,3.0f", 518, 61536, R.string.msg0000833, R.string.msg0020991),
    BRISK_STEPS = "516"  # ("%1$,3.0f", 516, 61536, R.string.msg0000833, R.string.msg0020991),
    KCAL_WALKING = "545"  # ("%1$,3.0f", 545, 16387, R.string.msg0000824, R.string.msg0020988),
    KCAL_ACTIVITY = "546"  # ("%1$,3.0f", 546, 16387, R.string.msg0000824, R.string.msg0020988),
    KCAL_FAT_BURNED = "579"  # ("%.1f", 579, 8192, R.string.msg0000852, R.string.msg0020990),
    KCAL_ALLDAY = "548"  # ("%1$,3.0f", 548, 16387, R.string.msg0000824, R.string.msg0020988),
    KM_FIGURE = "3"  # ("%.1f", 3, 4099, R.string.msg0000801, R.string.msg0020992),
    KM_DISTANCE = "576"  # ("%.1f", 576, 4099, R.string.msg0000801, R.string.msg0020992),
    TIME_SLEEP_START = "1025"  # ("%d", 1025, 0, -1, -1),
    TIME_SLEEP_ONSET = "1026"  # ("%d", 1026, 0, -1, -1),
    TIME_SLEEP_WAKEUP = "1027"  # ("%d", 1027, 0, -1, -1),
    TIME_SLEEPING = "1028"  # ("%d", 1028, 61488, R.string.msg0000866, R.string.msg0000866),
    TIME_SLEEPING_EFFICIENCY = "1029"  # ("%.1f", 1029, 61584, R.string.msg0000817, R.string.msg0000817),
    TIME_SLEEP_AROUSAL = "1030"  # ("%d", 1030, 61504, R.string.msg0000867, R.string.msg0000867),
    TEMPERATURE_BASAL = "1281"  # ("%.2f", 1281, 12288, R.string.msg0000823, R.string.msg0020972),
    FAHRENHEIT_TEMPERATURE_BASAL = "1281"  # ("%.2f", 1281, 12304, R.string.msg0000829, R.string.msg0020996),
    THERMOMETER_TEMPERATURE = "4866"  # ("%.1f", 4866, 12288, R.string.msg0000823, R.string.msg0020972),
    FAHRENHEIT_THERMOMETER_TEMPERATURE = "4866"  # ("%.1f", 4866, 12304, R.string.msg0000829, R.string.msg0020996),
    THERMOMETER_MEASUREMENT_MODE_PREDICTED = "4869"  # ("%.0f", 4869, -1, -1, -1),
    THERMOMETER_MEASUREMENT_MODE_MEASURED = "4870"  # ("%.0f", 4870, -1, -1, -1),
    MENSTRUATION_RECORD = "61442"  # ("%.0f", 61442, -1, -1, -1),
    MILE_FIGURE = "576"  # ("%.1f", 576, 4112, R.string.msg0000802, R.string.msg0020997),
    KCAL_DAY = "544"  # ("%1$,3.0f", 544, 16387, R.string.msg0000824, R.string.msg0020988),
    KCAL_FIGURE = "3"  # ("%1$,3.0f", 3, 16387, R.string.msg0000824, R.string.msg0020988),
    EVENT_RECORD = "61441"  # ("%d", 61441, 0, -1, -1),
    MMHG_MEAN_ARTERIAL_PRESSURE_FIGURE = "16"  # ("%1$,3.0f", 16, 20496, R.string.msg0000808, R.string.msg0020959),
    KPA_MEAN_ARTERIAL_PRESSURE_FIGURE = "16"  # ("%.1f", 16, 20483, R.string.msg0000809, R.string.msg0020993),
    AFIB_DETECT_FIGURE = "35"  # ("%.1f", 35, -1, -1, -1),
    AFIB_MODE_FIGURE = "39"  # ("%.1f", 39, -1, -1, -1),
    ECG_BPM_FIGURE = "4143"  # ("%1$,3.0f", 4143, 61600, R.string.msg0000815, R.string.msg0020960),
    SPO2_OXYGEN_SATURATION = "1537"  # ("%.0f", 1537, 61584, R.string.msg0000817, R.string.msg0000817),
    SPO2_PULSE_RATE = "1538"  # ("%.0f", 1538, 61600, R.string.msg0000815, R.string.msg0020960),
    THERMOMETER_TEMPERATURE_TYPE = "4871"  # ("%.0f", 4871, -1, -1, -1)


class DeviceCategory(enum.StrEnum):
    BPM = "0"
    SCALE = "1"
    # ACTIVITY = "2"
    # THERMOMETER = "3"
    # PULSE_OXIMETER = "4"


@dataclass(kw_only=True, match_args=True)
class AuthResponse(U.DataclassBase):
    id: str  # guid
    access_token: str
    refresh_token: str
    expires_in: int = 3600
    token_type: str = "Bearer"


@dataclass(kw_only=False, match_args=True)
class BodyIndexList(U.DataclassBase):
    value: int
    subtype: int  # unit/format ?
    unknown1: int
    unknown2: int

    def __post_init__(self):
        for field in ["value", "subtype", "unknown1", "unknown2"]:
            setattr(self, field, int(getattr(self, field)))


@dataclass(kw_only=True, match_args=True)
class Measurement(U.DataclassBase):
    def __post_init__(self):
        for k, v in self.bodyIndexList.items():
            self.bodyIndexList[k] = BodyIndexList(*v)

    transferDate: int
    measureDateFrom: int
    measureDateTo: int
    measureDeviceDateFrom: str
    measureDeviceDateTo: str
    userUpdateDate: int
    timeZone: str
    bodyIndexList: T.Dict[ValueType, BodyIndexList]
    clientAppId: int
    measurementMode: int


########################################################################################################################


def ble_mac_to_serial(mac: str) -> str:
    # e.g. 11:22:33:44:55:66 to 665544feff332211
    values = mac.split(":")
    serial = "".join(values[5:2:-1] + ["fe", "ff"] + values[2::-1])
    return serial.lower()


########################################################################################################################


class OmronDevice:
    def __init__(
        self, name: str, macaddr: str, category: T.Union[DeviceCategory, str], user: int = 1, enabled: bool = True
    ):
        self._name = name
        self._macaddr = macaddr
        self._serial = ble_mac_to_serial(macaddr)
        self._category = (
            category if isinstance(category, DeviceCategory) else DeviceCategory.__members__[category.upper()]
        )
        self._user = user
        self._enabled = enabled

    def __repr__(self):
        return (
            f"OmronDevice(name='{self.name}' serial='{self.serial}', category='{self.category.name}', user={self.user})"
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def macaddr(self) -> str:
        return self._macaddr

    @property
    def serial(self) -> str:
        return self._serial

    @property
    def category(self) -> DeviceCategory:
        return self._category

    @property
    def user(self) -> int:
        return self._user

    @property
    def enabled(self) -> bool:
        return self._enabled


########################################################################################################################


class OmronConnect:
    _APP_URL = f"/api/apps/{_OMRON_APP_ID}/server-code"

    def __init__(self, server: str):
        self.headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": _USER_AGENT,
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "X-OGSC-SDK-Version": _OGSC_SDK_VERSION,
            "X-OGSC-App-Version": _OGSC_APP_VERSION,
            "X-Kii-AppID": _OMRON_APP_ID,
            "X-Kii-AppKey": _OMRON_API_KEY,
        }
        self._server = server

    def login(self, username: str, password: str) -> T.Optional[AuthResponse]:
        authData = {
            "username": username,
            "password": password,
        }
        r = httpx.post(f"{self._server}/api/oauth2/token", json=authData, headers=self.headers)
        r.raise_for_status()

        authResponse = AuthResponse.from_dict(r.json())
        if authResponse:
            self.headers["authorization"] = f"Bearer {authResponse.access_token}"
            return authResponse

        return None

    def refresh_oauth2(self, refresh_token: str) -> T.Optional[AuthResponse]:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        r = httpx.post(f"{self._server}/api/oauth2/token", json=data, headers=self.headers)
        r.raise_for_status()

        authResponse = AuthResponse.from_dict(r.json())
        if authResponse:
            self.headers["authorization"] = f"Bearer {authResponse.access_token}"
            return authResponse

        return None

    def get_me(self) -> T.Dict[str, T.Any]:
        r = httpx.get(f"{self._server}{self._APP_URL}/users/me", headers=self.headers)
        r.raise_for_status()
        return r.json()

    # utc timestamps
    def get_measurements(
        self, device: OmronDevice, searchDateFrom: int = 0, searchDateTo: int = 0
    ) -> T.List[Measurement]:
        data = {
            "containCorrectedDataFlag": 1,
            "containAllDataTypeFlag": 1,
            "deviceCategory": device.category,
            "deviceSerialID": device.serial,
            "userNumberInDevice": int(device.user),
            "searchDateFrom": searchDateFrom if searchDateFrom >= 0 else 0,
            "searchDateTo": int(U.utcnow().timestamp() * 1000) if searchDateTo <= 0 else searchDateTo,
            # "deviceModel": "OSG",
        }

        r = httpx.post(f"{self._server}{self._APP_URL}/versions/current/measureData", json=data, headers=self.headers)
        r.raise_for_status()

        resp = r.json()
        L.debug(resp)

        returnedValue = resp["returnedValue"]
        try:
            if isinstance(returnedValue, list):
                returnedValue = returnedValue[0]
            if "errorCode" in returnedValue:
                L.error(f"get_measurements() -> {returnedValue}")
                return []
        except KeyError:
            pass

        if _debugSaveResponse:
            fname = f".debug/{data['searchDateTo']}_{device.serial}_{device.user}.json"
            U.json_save(fname, returnedValue)

        measurements: T.List[Measurement] = []
        devCat = DeviceCategory(returnedValue["deviceCategory"])
        deviceModelList = returnedValue["deviceModelList"]
        if deviceModelList is None:
            return measurements

        for devModel in deviceModelList:
            deviceModel = devModel["deviceModel"]
            deviceSerialIDList = devModel["deviceSerialIDList"]
            for dev in deviceSerialIDList:
                deviceSerialID = dev["deviceSerialID"]
                user = dev["userNumberInDevice"]
                L.debug(f" - deviceModel: {deviceModel} category: {devCat.name} serial: {deviceSerialID} user: {user}")

                if deviceSerialID == device.serial:
                    measurements = [Measurement(**m) for m in dev["measureList"]]
                    break

        return measurements


########################################################################################################################
