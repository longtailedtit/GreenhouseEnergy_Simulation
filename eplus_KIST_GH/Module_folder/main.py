import subprocess
import pandas as pd
from datetime import datetime, timedelta
from Schedule_setting_hgminivalidation import write_idf_setpoints, run_simulation
import warnings
warnings.filterwarnings(action='ignore')

"""

"""

# 시뮬레이션 기간(RunPeriod)
SM = 4 #시작월
SD = 21 #시작일
EM = 4 #종료월
ED = 30 #종료일
TS = 6 #타임스텝(결과출력주기)  1: 시간별, 2, 30분별, 4: 15분별, 6: 10분별

# file and path
weather_file = "/home/agtech_eplus/eplus_KIST_GH/KOR_KW_Daegwallyeong.471000_TMYx.2007-2021.epw"

eplus_path = "/usr/local/EnergyPlus-23-1-0/energyplus-23.1.0"
idf_base_path = "/home/agtech_eplus/eplus_KIST_GH/idf_world/Eplus_HG_kist_SetpointVer(KIST_HG_ver3)_modify_forvail_0502.idf"
idf_custom_path = "/home/agtech_eplus/eplus_KIST_GH/modify_addvali0502_3.idf"
eplus_file = "/home/agtech_eplus/eplus_KIST_GH/modify_addvali0502_3.idf"
out_files = "/home/agtech_eplus/eplus_KIST_GH/"

out_name = 'modify_addvali0502_3'

### (1) 시뮬레이션 설정, 스케줄 값을 받아 idf 파일에 온실 세팅값 작성
write_idf_setpoints(idf_base_path, idf_custom_path, SM, SD, EM, ED, TS)

### (2) 시뮬레이션 실행
output_csv, output_mtr = run_simulation(eplus_path, weather_file, eplus_file, out_files, out_name)

### (3) 결과값 처리
def make_EnvResultsFile(output_csv,TS,out_name): # 환경값 정리
    depout = pd.read_csv(output_csv)
    depout['Date/Time'] = depout['Date/Time'].str.strip() # 공백 제거 및 형식 확인

    # timestep(TS)에 따른 filter 걸기
    time_filter = {
        1: '01/01  01:00:00',
        2: '01/01  00:30:00',
        4: '01/01  00:15:00',
        6: '01/01  00:10:00' # 시뮬레이션 시기 바꾸면 각 ts에 따라 날짜도 변경해줘야함
    }

    filter_time = time_filter.get(TS, 'None') # 선택한 timestep을 선택
    filter_idx = depout[depout['Date/Time'] == filter_time].index # 실제 시뮬레이션이 시작하는 시간의 인덱스를 골라 잘라내기
    # drop
    first_idx = filter_idx[0]
    filtered_df = depout.loc[first_idx:]
    filtered_df.reset_index(drop=True,inplace=True)

    # 환경값 파일에 필요한 컬럼들만 골라내기
    need_column = ['Date/Time','Environment:Site Outdoor Air Drybulb Temperature [C](TimeStep)'
                ,'Environment:Site Outdoor Air Relative Humidity [%](TimeStep)','Environment:Site Wind Speed [m/s](TimeStep)'
                ,'Environment:Site Diffuse Solar Radiation Rate per Area [W/m2](TimeStep)'
                ,'Environment:Site Direct Solar Radiation Rate per Area [W/m2](TimeStep)'
                ,'THERMAL ZONE BOTTOM:Zone Air Temperature [C](TimeStep)'
                ,'THERMAL ZONE BOTTOM:Zone Air Relative Humidity [%](TimeStep)'
                ,'SPACE TOP:Zone Windows Total Transmitted Solar Radiation Rate [W](TimeStep)']
    envio = filtered_df[need_column]

    # 이름 바꾸기
    envio.columns = ['date','Out_Temp[C]','Out_Humid[%]','WindSP[m/s]','Diffuse_Radiation[W/m2]','Direct_Radiation[W/m2]','In_Temp[C]','In_Humid[%]','In_Radiation[W/m2]']
    envio["Radiation[W/m2]"] = envio['Diffuse_Radiation[W/m2]'] + envio['Direct_Radiation[W/m2]'] # 직달일사+확산일사
    envio = envio.drop(columns=['Diffuse_Radiation[W/m2]','Direct_Radiation[W/m2]'])

    envio_file = 'trial_'+out_name+'_envdata.csv'
    envio.to_csv(envio_file, index=False)

    return envio_file

def Calculate_Energy(output_mtr): # 에너지값 정리
    mtrout = pd.read_csv(output_mtr)

    idx = 228
    mtr_engy = mtrout.iloc[idx:]
    mtr_engy.reset_index(drop=True,inplace=True)

    pd.options.display.float_format = '{:.3f}'.format # 지수표기로 된 숫자를 변환한다.
    mtr_engy.columns = ['date','Fan_elecE(J)','Pumps_elecE(J)','FuelOilE(J)']

    # 1KJ = 1000J, 1MJ = 1000000J
    mtr_engy.loc[:,'Fan_elecE(MJ)'] = mtr_engy['Fan_elecE(J)'] / 1000000
    mtr_engy.loc[:,'Pumps_elecE(MJ)'] = mtr_engy['Pumps_elecE(J)'] / 1000000
    mtr_engy.loc[:,'FuelOilE(MJ)'] = mtr_engy['FuelOilE(J)'] / 1000000

    electricity = (mtr_engy['Fan_elecE(MJ)'].sum() + mtr_engy['Pumps_elecE(MJ)'].sum()).round(2) # 전력에 사용되는 두 항목을 합침
    fuelOilE = mtr_engy['FuelOilE(MJ)'].sum().round(2)

    return electricity, fuelOilE

envio_file = make_EnvResultsFile(output_csv,TS,out_name)
electricity, fuelOilE = Calculate_Energy(output_mtr)

print(envio_file) # 정리된 환경값 파일 이름 알려줌(trial_**_envdata)
print(electricity)
print(fuelOilE)