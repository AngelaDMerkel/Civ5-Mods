"""The two independent release packages and their stable identities."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BNW_ID = '6DA07636-4123-4018-B643-6575B4EC336B'
RT_ID = 'd571e16c-bb58-40bf-a81f-a919249e7995'
RO_ID = '4547ae42-3d17-4993-99e8-a7a5a2c1ec2c'
PACKAGES = [
    dict(source=ROOT/'mod', name='Realistic Terrain', slug='Realistic-Terrain', version=2, id=RT_ID,
         description='Environmental exposure, cooperative trade logistics and connected desert irrigation. Build Irrigation Works, irrigated farms, the Ministry of Coin, road-connected Caravansaries and patrols. Optional Resource Outposts integration shelters its stationed defenders. Requires Brave New World. Single-player alpha; start a new game.',
         actions=['Text/RT_Text.xml','SQL/RT_Promotions.sql','SQL/RT_ReliefStation.sql','SQL/RT_MinistryOfCoin.sql','SQL/RT_Trade.sql','SQL/RT_MotorizedCaravan.sql','SQL/RT_Irrigation.sql','SQL/RT_Art.sql'], entry='UI/RT_Environment.xml'),
    dict(source=ROOT/'outposts', name='Resource Outposts', slug='Resource-Outposts', version=1, id=RO_ID,
         description='Independent worker-built outposts claim neutral strategic and luxury deposits. Includes an outpost overview, upkeep, abandonment previews, territorial conversion, resource notifications and AI expeditions with escorts, recovery and stalled-order handling. No roads or supply connections required. Optional Realistic Terrain integration adds garrison shelter only. Requires Brave New World. Single-player alpha; start a new game.',
         actions=['Text/RO_Text.xml','SQL/RO_Outposts.sql'], entry='UI/RO_UI.xml'),
]
