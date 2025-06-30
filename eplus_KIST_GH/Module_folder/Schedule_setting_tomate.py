import pandas as pd
from datetime import datetime, timedelta
import subprocess

"""
* 토마토 농가 데이터(농진청 최적환경설정 서비스)를 참고하여 설정한 setpoint
"""

# 각 월별 일출/일몰 시간
sunrise_times = {1: '7:30', 2: '7:00', 3: '6:30', 4: '6:00', 5: '5:30', 6: '5:00'}
sunset_times = {1: '17:30', 2: '18:00', 3: '18:30', 4: '19:00', 5: '19:30', 6: '20:00'}

# month to str
def MonthToName(mon):
        month_names = ['Jan','Feb','Mar','Apr','May','Jun']
        return month_names[mon - 1]

# time to datetime
def TimeToDatetime(time_str):
        return datetime.strptime(time_str,"%H:%M")

# datetime to str
def DatetimeToStr(time_obj):
        return time_obj.strftime("%H:%M")

# calculate datetime
def CalculateDatetime(time_str, hours):
        time_obj = TimeToDatetime(time_str)
        new_time_obj = time_obj - timedelta(hours=hours)
        return DatetimeToStr(new_time_obj)

### idf 수정 구간
def write_idf_setpoints(idf_base_path, idf_custom_path, SM, SD, EM, ED, TS):
       with open(idf_base_path, 'r') as file:   #idf가 있는 패스
        data = file.readlines()
#        line=data[178]
        data[78] = 'Timestep,%s; \n'%TS    # 아웃풋 출력주기
        data[3524] = '  %s,    !- Begin Month\n' %SM   #시뮬레이션 하고 싶은 시작월
        data[3525] = '  %s,    !- Begin Day of Month \n'%SD    #시뮬레이션 하고 싶은 시작일
        data[3527] = '  %s,    !- End Month \n'%EM    #시뮬레이션 끝내고 싶은 종료 월
        data[3528] = '  %s,    !- End Day of Month \n'%ED    #시뮬레이션 끝내고 싶은 종료 일

        for mon in range(SM,EM+1):
               month_end = MonthToName(mon)
               sunrise = sunrise_times[mon]
               sunset = sunset_times[mon]

               setpoint, times = month_schedule_setpoints(mon, sunrise, sunset)
               setpoint_df = pd.DataFrame({
                     'schedule_name': [f'Schedule Day 4_{month_end}',f'Schedule Day 7_{month_end}',f'Humid Setpoint Schedule_{month_end}',f'VentCool_{month_end}',f'Schedule Day 2_{month_end}'],
                     'times': times,
                     'setpoint': setpoint
               })

               Modify_ScheduleDay(f"Schedule Day 4_{month_end},", setpoint_df,data)
               Modify_ScheduleDay(f"Schedule Day 7_{month_end},", setpoint_df,data)
               # Modify_ScheduleDay(f"Humid Setpoint Schedule_{month_end},", setpoint_df,data)
               Modify_ScheduleDay(f"VentCool_{month_end},", setpoint_df,data)
               Modify_ScheduleDay(f"Schedule Day 2_{month_end},", setpoint_df,data)

        AirflowNetwork_setpoints(data, "Thermal Zone Top", 0.2, 7, 30)

        with open(idf_custom_path, 'w') as file:
               file.writelines(data)
               # file.close()


def month_schedule_setpoints(mon, sunrise, sunset): # 각 월별 setpoint와 시간대 구간을 설정하는 함수
    # 순서[list_index]: heating[0] - shading[1] - humid[2] - venting[3] - fog[4]
    setpoint_data = {
          1: [['14.0','16.8','16.8','20.5','20.5','17.4','17.4','14.0','14.0'],['0','1','0'],['87.3','87.5','85.5','80.0','86.5','88.6','87.3'],['18.5','21.8','21.8','26.5','26.5','22.8','22.8','18.5','18.5'],['1']],
          2: [['14.0','16.8','16.8','20.5','20.5','17.4','17.4','14.0','14.0'],['0','1','0'],['87.3','87.5','85.5','80.0','86.5','88.6','87.3'],['18.5','21.8','21.8','26.5','26.5','22.8','22.8','18.5','18.5'],['1']],
          3: [['16.0','19.3','19.3','23.8','23.8','20.1','20.1','16.0','16.0'],['0','1','0'],['88.6','89.6','81.0','68.7','78.7','85.3','88.6'],['20.5','25.0','25.0','29.8','29.8','25.7','25.7','20.5','20.5'],['1']],
          4: [['16.0','19.3','19.3','23.8','23.8','20.1','20.1','16.0','16.0'],['0','1','0'],['88.6','89.6','81.0','68.7','78.7','85.3','88.6'],['20.5','25.0','25.0','29.8','29.8','25.7','25.7','20.5','20.5'],['1']],
          5: [['21.7','24.5','24.5','28.2','28.2','24.8','24.8','21.7','21.7'],['0','1','0'],['88.6','89.6','81.0','68.7','78.7','85.3','88.6'],['26.2','29.5','29.5','34.2','34.2','29.8','29.8','26.2','26.2'],['1']],
          6: [['21.7','24.5','24.5','28.2','28.2','24.8','24.8','21.7','21.7'],['0','1','0'],['90.6','92.5','80.4','67.1','75.8','85.3','90.6'],['26.2','29.5','29.5','34.2','34.2','29.8','29.8','26.2','26.2'],['1']],
    }
    times_data = {
          1: [[CalculateDatetime(sunrise,2),sunrise,'11:00','12:00',CalculateDatetime(sunset,3),CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00'],[sunrise,sunset,'24:00']
              ,[CalculateDatetime(sunrise,2),sunrise,'12:00',CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00']
              ,[CalculateDatetime(sunrise,2),sunrise,'11:00','12:00',CalculateDatetime(sunset,3),CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00'],['24:00']],
          2: [[CalculateDatetime(sunrise,2),sunrise,'11:00','12:00',CalculateDatetime(sunset,3),CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00'],[sunrise,sunset,'24:00']
              ,[CalculateDatetime(sunrise,2),sunrise,'12:00',CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00']
              ,[CalculateDatetime(sunrise,2),sunrise,'11:00','12:00',CalculateDatetime(sunset,3),CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00'],['24:00']],
          3: [[CalculateDatetime(sunrise,2),sunrise,'11:00','12:00',CalculateDatetime(sunset,3),CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00']
              ,[sunrise,sunset,'24:00'],[CalculateDatetime(sunrise,2),sunrise,'12:00',CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00']
              ,[CalculateDatetime(sunrise,2),sunrise,'11:00','12:00',CalculateDatetime(sunset,3),CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00'],['24:00']],
          4: [[CalculateDatetime(sunrise,2),sunrise,'11:00','12:00',CalculateDatetime(sunset,3),CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00']
              ,[sunrise,sunset,'24:00'],[CalculateDatetime(sunrise,2),sunrise,'12:00',CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00']
              ,[CalculateDatetime(sunrise,2),sunrise,'11:00','12:00',CalculateDatetime(sunset,3),CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00'],['24:00']],
          5: [[CalculateDatetime(sunrise,2),sunrise,'11:00','12:00',CalculateDatetime(sunset,3),CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00']
              ,[sunrise,sunset,'24:00'],[CalculateDatetime(sunrise,2),sunrise,'12:00',CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00']
              ,[CalculateDatetime(sunrise,2),sunrise,'11:00','12:00',CalculateDatetime(sunset,3),CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00'],['24:00']],
          6: [[CalculateDatetime(sunrise,2),sunrise,'11:00','12:00',CalculateDatetime(sunset,3),CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00']
              ,[sunrise,sunset,'24:00'],[CalculateDatetime(sunrise,2),sunrise,'12:00',CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00']
              ,[CalculateDatetime(sunrise,2),sunrise,'11:00','12:00',CalculateDatetime(sunset,3),CalculateDatetime(sunset,2),sunset,CalculateDatetime(sunset,-2),'24:00'],['24:00']], 
    }

    ### 조정하고 싶은 조건들(어떤 월을 바꿀 것인지, category, setpoint 조정값)
#     adjustments = [
#           (list(range(1,7)),3,-2),
#     ]

    def adjust_setpoints(adjustments):
       for adj in adjustments:
             mon_range, list_index, adjust_number = adj
             for mon in mon_range:
                   setpoint_data[mon][list_index] = [str(float(value) + adjust_number) for value in setpoint_data[mon][list_index]]
              
       return setpoint_data
    
    ### setpoint를 조정 실행
#     setpoint_data = adjust_setpoints(adjustments)

    return setpoint_data[mon], times_data[mon]
        

def Modify_ScheduleDay(obj_name, inform_df, data):  # Schedule:Day:Interval의 값을 수정할 수 있는 함수
        # Schedule:Day:Interval가 포함된 줄 찾기
        for i, line in enumerate(data):
                if "Schedule:Day:Interval," in line:
                        next_index = i + 1      # Schedule:Day:Interval, 다음 줄 field로 name이 오기 때문에 i + 1

                        # 원하는 이름(!- Name) 찾기
                        if obj_name in data[next_index]:
                                start_index = i + 4   # 수정할 setpoint의 index
                                field_value = 1    # 시간이 수정되는 Time 1 부터 시작
                                value_col = obj_name.split(',')[0]

                                # 데이터프레임 내 setting value를 삽입하기
                                for j, row in inform_df.iterrows():
                                        if row['schedule_name'] == value_col:
                                                if row['schedule_name'] == value_col:
                                                        count_line = 0
                                                        for idx, (time,set_value) in enumerate(zip(row['times'], row['setpoint'])):
                                                                insert_index = start_index + count_line   # 들어가야 할 위치를 찾는다

                                                                data.insert(insert_index, '    %s,                   !- Time %d {hh:mm}\n'%(time,idx + 1))
                                                                count_line += 1

                                                                if idx == len(row['times']) - 1:    # field값 마지막에는 ;이 들어가기 때문에 마지막 줄이면 다른 양식(;)을 쓰도록 지시
                                                                        data.insert(insert_index + 1, '    %s;                      !- Value Until Time %d\n'%(set_value,idx + 1))
                                                                else:
                                                                        data.insert(insert_index + 1, '    %s,                      !- Value Until Time %d\n'%(set_value,idx + 1))
                                                                count_line += 1

                                                        # 기존값 삭제하기
                                                        del_index = start_index + count_line  # insert 마친 지점
                                                        while data[del_index].strip():            # 공백이 나타날때까지 지우기
                                                                del data[del_index]

def AirflowNetwork_setpoints(data, obj_name, min_open_factor, temp_diff_lower_limit, temp_diff_upper_limit):
       for i, line in enumerate(data):
              if "AirflowNetwork:MultiZone:Zone," in line:
                     next_index = i + 1
                     
                     # 원하는 이름 찾기
                     if obj_name in data[next_index]:
                            for j in range(i + 1, len(data)):
                                if "Minimum Venting Open Factor {dimensionless}" in data[j]:
                                   data[j] = f"    {min_open_factor},                     !- Minimum Venting Open Factor {{dimensionless}}\n"
                                elif "Temperature Difference Lower Limit" in data[j]:
                                   data[j] = f"    {temp_diff_lower_limit},                       !- Indoor and Outdoor Temperature Difference Lower Limit For Maximum Venting Open Factor {{deltaC}}\n"
                                elif "Temperature Difference Upper Limit" in data[j]:
                                   data[j] = f"    {temp_diff_upper_limit},                     !- Indoor and Outdoor Temperature Difference Upper Limit for Minimum Venting Open Factor {{deltaC}}\n"
                                elif "Natural Window Schedule" in data[j]:
                                   break
                            break


def run_simulation(eplus_path, weather_file, eplus_file, out_files, out_name):
       df = subprocess.Popen([eplus_path, "-w", weather_file, "-d", out_files, "-p", out_name, "-r", eplus_file], stdout=subprocess.PIPE, shell =False)
       output, err = df.communicate()

       return f"{out_files}{out_name}out.csv", f"{out_files}{out_name}mtr.csv"