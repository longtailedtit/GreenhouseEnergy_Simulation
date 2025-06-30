# EnergyPlus for Greenhouse(HG_KIST)

## IDF File
### Eplus_HG_kist_SetpointVer(KIST_HG_ver3)
: KIST_ Hoenggye_original에 대한 주요 변경 사항

### **1. Schedule**
- **ScheduleTypeLimits**: Humidity(%) 일정 유형 추가 (0-100%) 범위  
- **온실 구동기에 대한 작동 스케줄 정의**
    - Schedule Day 4  
    : 난방 시스템. Heating Setpoint Schedule, Timestep 사이의 값을 선형보간(Linear)
    - Schedule Day 2  
    : 포그 시스템. Fog Operation Schedule
    - Schedule Day 7  
    : 차광 시스템(스크린). WindowShadingControl
    - VentCool, Fog Humid Schedule  
    : 습도와 관련된 스케줄. 실험에서 사용하진 않음
    - 시뮬레이션 기간 동안 월별로 작동 스케줄을 정의할 수 있도록 설정 **Schedule:Week:Daily, Schedule:Year**

### **2. Control**  

- **AirflowNetwork:MultiZone:Zone,** : 천창 개폐와 관련된 설정  
    - Temperature,  !- Ventilation Control Mode
        - 실내외 온도차 기반 환기 제어
- **ZoneHVAC:EquipmentList,**
    - 0,   !- Zone Equipment 1 Cooling Sequence  
        - 해당 장비는 Cooling Sequence에 대해서 처리하지 않음

### **3. Output Files**  
> 출력 보고서(Table)에 총 에너지 소비의 월별 테이블을 출력(합계 또는 평균)

    Output:Table:Monthly,
       TotalEnergy:Facility,  !- Variable or Meter 1 Name
       SumOrAverage;          !- Aggregation Type for Variable or Meter 1

> OUTPUT:VARIABLE - 출력 변수들

    Output:Variable,*,Zone Air Temperature,Timestep;
    Output:Variable,*,Zone Air Relative Humidity,Hourly;
    Output:Variable,*,Zone Air Relative Humidity,Timestep;
    Output:Variable,*,Site Outdoor Air Drybulb Temperature,Hourly;
    Output:Variable,*,Site Outdoor Air Drybulb Temperature,Timestep;
    Output:Variable,*,Site Outdoor Air Relative Humidity,Hourly;
    Output:Variable,*,Site Outdoor Air Relative Humidity,Timestep;
    Output:Variable,*,Fan Electricity Energy,Timestep;
    Output:Variable,*,Facility Total Electricity Demand Rate,Timestep;
    Output:Variable,*,Boiler Heating Energy,Timestep;
    Output:Variable,*,Boiler FuelOilNo2 Energy,Timestep;
    Output:Variable,*,Pump Electricity Energy,Timestep;
    Output:Variable,*,Site Diffuse Solar Radiation Rate per Area,Timestep;
    Output:Variable,*,Site Direct Solar Radiation Rate per Area,Timestep;
    Output:Variable,*,Site Wind Speed,Timestep;
    Output:Variable,*,Zone Windows Total Transmitted Solar Radiation Rate,Timestep;
    Output:Variable,*,Facility Heating Setpoint Not Met Time,Timestep;
    Output:Variable,*,AFN Surface Venting Window or Door Opening Factor,Timestep;
    Output:Variable,*,AFN Surface Venting Window or Door Opening Modulation Multiplier,Timestep;
    Output:Variable,*,AFN Surface Venting Inside Setpoint Temperature,Timestep;
    Output:Variable,*,Zone Thermostat Heating Setpoint Temperature,Timestep;
    Output:Variable,*,Surface Shading Device Is On Time Fraction,Timestep;
    Output:Variable,*,Schedule Value,Timestep;

> Output:Meter - 에너지와 관련된 출력 변수들   

    Output:Meter,Fans:Electricity,Monthly;
    Output:Meter,Pumps:Electricity,Monthly;
    Output:Meter,FuelOilNo2:Facility,Monthly;

### KIST_HG_Add_Plant(original), KIST_HG_Add_Plant(ver4.0)
: 작물 관련 수식이 포함된 원본 파일(original), KIST_HG_ver3의 내용을 추가한 파일(ver4.0)

### Eplus_HG_kist_SetpointVer(KIST_HG_ver3)_modify
: KIST_HG_ver3에서 온실 자재(철제프레임)에 대한 물성 정정

    Material:steel Material
        0.075,                   !- Thickness {m}
        52,                      !- Conductivity {W/m-K}
        7800,                    !- Density {kg/m3}
        470,                     !- Specific Heat {J/kg-K}

## Running Simulations
### Main 
: 시뮬레이션 실행을 위한 설정 파일. 스케줄 설정 파일(Schedule_setting*을 불러와 정보 받음)

**1. 온실 세팅값을 idf에 작성**
- 시뮬레이션 기간(시작월/일, 종료월/일) 지정  
- 파일 경로(idf,epws) 지정  
- write_idf_setpoints 함수 실행  

**2. 시뮬레이션 실행**  
- 에너지플러스 시뮬레이션 실행
- 결과 파일로 **output_csv**(환경값+output 변수), **output_mtr**(에너지값)  

**3. 결과 파일 정리**  
- make_EnvResultsFile: output_csv 파일에서 온실 환경 값 추출하여 정리  
- Calculate_Energy: 출력된 에너지 값 단위를 MJ로 계산, 전력값과 등유값의 총합 출력(간단히 확인)  

### Schedule_setting_* 
: 시뮬레이션에 설정하는 시나리오에 대한 스케줄을 설정하는 파일.  

**1. 각 월별 일출/일몰 시간에 따라 스케줄을 설정하기 위한 시간 계산**  

**2. IDF 파일 읽고 수정하기**  
- 각 월별 setpoint와 시간대 설정, 시나리오 내에서 설정 조정 가능(바꾸고 싶은 달의 setting 종류, 값)    
- Schedule:Day:Interval 값 수정(idf에 스케줄 설정사항 작성)  
- AirflowNetwork(천창관련) 설정 수정 가능  

**3. 시뮬레이션 실행하기**  