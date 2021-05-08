import enum

from lation.modules.spot_perp_bot.env import \
    FTX_API_KEY_ME, FTX_API_SECRET_ME, \
    FTX_API_KEY_MOM, FTX_API_SECRET_MOM, \
    FTX_API_KEY_SISTER, FTX_API_SECRET_SISTER


enum_map = {}

if FTX_API_KEY_ME and FTX_API_SECRET_ME:
    enum_map['我'] = '期现套利子帳戶'

if FTX_API_KEY_MOM and FTX_API_SECRET_MOM:
    enum_map['媽媽'] = '媽媽'

if FTX_API_KEY_SISTER and FTX_API_SECRET_SISTER:
    enum_map['姊姊'] = '姊姊'

SubaccountNameEnum = enum.Enum('SubaccountNameEnum', enum_map)
