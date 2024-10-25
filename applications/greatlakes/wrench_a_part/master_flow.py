import pprint

import psycopg2
import requests
from prefect import flow, task, variables
from prefect.blocks.system import Secret
import datetime

import json
import requests
import pprint
from common import *
from psycopg2.extensions import AsIs
@task
def create_table():
    with connect_to_db() as conn:
        cur = conn.cursor()
        cur.execute("CREATE schema if not exists raw;")
        cur.execute('''CREATE TABLE if not exists raw.wrenchapart (
                            yard varchar,
                            make_id integer,
                            model_id integer,
                            photo text,
                            color varchar,
                            stockNumber varchar primary key,
                            dateAdded timestamp,
                            row integer,
                            ABS text,
                            ActiveSafetySysNote text,
                            AdaptiveCruiseControl text,
                            AdaptiveDrivingBeam text,
                            AdaptiveHeadlights text,
                            AdditionalErrorText text,
                            AirBagLocCurtain text,
                            AirBagLocFront text,
                            AirBagLocKnee text,
                            AirBagLocSeatCushion text,
                            AirBagLocSide text,
                            AutoReverseSystem text,
                            AutomaticPedestrianAlertingSound text,
                            AxleConfiguration text,
                            Axles text,
                            BasePrice text,
                            BatteryA text,
                            BatteryA_to text,
                            BatteryCells text,
                            BatteryInfo text,
                            BatteryKWh text,
                            BatteryKWh_to text,
                            BatteryModules text,
                            BatteryPacks text,
                            BatteryType text,
                            BatteryV text,
                            BatteryV_to text,
                            BedLengthIN text,
                            BedType text,
                            BlindSpotIntervention text,
                            BlindSpotMon text,
                            BodyCabType text,
                            BodyClass text,
                            BrakeSystemDesc text,
                            BrakeSystemType text,
                            BusFloorConfigType text,
                            BusLength text,
                            BusType text,
                            CAN_AACN text,
                            CIB text,
                            CashForClunkers text,
                            ChargerLevel text,
                            ChargerPowerKW text,
                            CoolingType text,
                            CurbWeightLB text,
                            CustomMotorcycleType text,
                            DaytimeRunningLight text,
                            DestinationMarket text,
                            DisplacementCC text,
                            DisplacementCI text,
                            DisplacementL text,
                            Doors text,
                            DriveType text,
                            DriverAssist text,
                            DynamicBrakeSupport text,
                            EDR text,
                            ESC text,
                            EVDriveUnit text,
                            ElectrificationLevel text,
                            EngineConfiguration text,
                            EngineCycles text,
                            EngineCylinders text,
                            EngineHP text,
                            EngineHP_to text,
                            EngineKW text,
                            EngineManufacturer text,
                            EngineModel text,
                            EntertainmentSystem text,
                            ErrorCode text,
                            ErrorText text,
                            ForwardCollisionWarning text,
                            FuelInjectionType text,
                            FuelTypePrimary text,
                            FuelTypeSecondary text,
                            GCWR text,
                            GCWR_to text,
                            GVWR text,
                            GVWR_to text,
                            KeylessIgnition text,
                            LaneCenteringAssistance text,
                            LaneDepartureWarning text,
                            LaneKeepSystem text,
                            LowerBeamHeadlampLightSource text,
                            Make text,
                            MakeID text,
                            Manufacturer text,
                            ManufacturerId text,
                            Model text,
                            ModelID text,
                            ModelYear text,
                            MotorcycleChassisType text,
                            MotorcycleSuspensionType text,
                            NCSABodyType text,
                            NCSAMake text,
                            NCSAMapExcApprovedBy text,
                            NCSAMapExcApprovedOn text,
                            NCSAMappingException text,
                            NCSAModel text,
                            NCSANote text,
                            NonLandUse text,
                            Note text,
                            OtherBusInfo text,
                            OtherEngineInfo text,
                            OtherMotorcycleInfo text,
                            OtherRestraintSystemInfo text,
                            OtherTrailerInfo text,
                            ParkAssist text,
                            PedestrianAutomaticEmergencyBraking text,
                            PlantCity text,
                            PlantCompanyName text,
                            PlantCountry text,
                            PlantState text,
                            PossibleValues text,
                            Pretensioner text,
                            RearAutomaticEmergencyBraking text,
                            RearCrossTrafficAlert text,
                            RearVisibilitySystem text,
                            SAEAutomationLevel text,
                            SAEAutomationLevel_to text,
                            SeatBeltsAll text,
                            SeatRows text,
                            Seats text,
                            SemiautomaticHeadlampBeamSwitching text,
                            Series text,
                            Series2 text,
                            SteeringLocation text,
                            SuggestedVIN text,
                            TPMS text,
                            TopSpeedMPH text,
                            TrackWidth text,
                            TractionControl text,
                            TrailerBodyType text,
                            TrailerLength text,
                            TrailerType text,
                            TransmissionSpeeds text,
                            TransmissionStyle text,
                            Trim text,
                            Trim2 text,
                            Turbo text,
                            VIN text,
                            ValveTrainDesign text,
                            VehicleDescriptor text,
                            VehicleType text,
                            WheelBaseLong text,
                            WheelBaseShort text,
                            WheelBaseType text,
                            WheelSizeFront text,
                            WheelSizeRear text,
                            Wheels text,
                            Windows text
                        );''')

@task
def get_existing():
    with connect_to_db() as conn:
        cursor = conn.cursor()
        cursor.execute("select stockNumber from raw.wrenchapart where vin is not null")
        return [i[0] for i in cursor.fetchall()]
@task
def remove_old(stock_nums):
    with connect_to_db() as conn:
        cursor = conn.cursor()
        cursor.execute("select stockNumber from raw.wrenchapart")
        deleted = [i[0] for i in cursor.fetchall() if i not in stock_nums]
        print(f"Deleting {len(deleted)} rows from DB")
        for stockNumber in deleted:
            cursor.execute('delete from raw.wrenchapart where stockNumber = %s', (stockNumber,))
@task
def load_database():
    insert_statement = 'insert into raw.wrenchapart (%s) values %s on conflict do nothing;'
    existing_stock = get_existing()
    keys = ['yard', 'photo', 'color', 'stockNumber', 'dateAdded', 'row', 'AirBagLocFront', 'AirBagLocSide', 'BedType', 'BodyCabType', 'BodyClass', 'BusFloorConfigType', 'BusType', 'CoolingType', 'CustomMotorcycleType', 'DisplacementCC', 'DisplacementCI', 'DisplacementL', 'Doors', 'DriveType', 'EngineConfiguration', 'EngineCycles', 'EngineCylinders', 'EngineHP', 'EngineHP_to', 'EngineManufacturer', 'EngineModel', 'ErrorCode', 'ErrorText', 'FuelTypePrimary', 'GVWR', 'GVWR_to', 'Make', 'MakeID', 'Manufacturer', 'ManufacturerId', 'Model', 'ModelID', 'ModelYear', 'MotorcycleChassisType', 'MotorcycleSuspensionType', 'PlantCity', 'PlantCompanyName', 'PlantCountry', 'PlantState', 'SeatBeltsAll', 'Series', 'TrailerBodyType', 'TrailerType', 'VIN', 'VehicleDescriptor', 'VehicleType', 'make_id', 'model_id']
    
    with connect_to_db() as conn:
        cursor = conn.cursor()
        vehicles = search(location_id=None, make_id=None, model_id=None)
        print(f"Got {len(vehicles)} from WAP API. {len(existing_stock)} already in DB")
        for vehicle in vehicles:
            if vehicle['stockNumber'] in existing_stock:
                continue
            row = enrich_vehicle(vehicle)
            values = [i if i else None for i in [row.get(k) for k in keys]]
            cursor.execute('delete from raw.wrenchapart where stockNumber = %s', (row['stockNumber'],))
            cursor.execute(insert_statement, (AsIs(','.join(keys)), tuple(values)))
            conn.commit()
        #remove_old([i['stockNumber'] for i in vehicles])

@task
def search(location_id=2, make_id=None, model_id=None):
	params = {}
	if location_id:
		params['locationId'] = location_id
	if make_id:
		params['makeId'] = make_id
	if model_id:
		params['modelId'] = model_id

	r = requests.get('https://api.wrenchapart.com/v1/vehicles', params=params)
	return r.json()

@task(retries=10, retry_delay_seconds=30)
def decode(vin):
    print(f"Decoding {vin}")
    r = requests.get(f'https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{vin}', params={'format':'json'})
    if r.status_code == 200:
        try:
            return {key:value for key, value in r.json()['Results'][0].items() if value}
        except KeyError:
            return {}
    else:
        raise Exception("Failed to get decoded VIN")
def enrich_vehicle(vehicle):
    vehicle.update(decode(vehicle['vin']))
    vehicle.update({
        'make_id': vehicle['make']['id'],
        'make': vehicle['make']['name'],
        'model_id': vehicle['model']['id'],
        'model': vehicle['model']['name'],
        'row': vehicle['row']['id']
    })

    return vehicle
@flow(log_prints=True)
def wap_master():
    create_table()
    load_database()


if __name__ == "__main__":
    wap_master.serve(name="wap-master", cron="0 0 * * *")
