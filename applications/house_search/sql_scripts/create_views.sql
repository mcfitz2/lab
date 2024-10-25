drop view if exists house_search.bakeries;
create view house_search.bakeries as 
select  data['name']::varchar as name, 
        data['place_id']::varchar as place_id,
		data['geometry']['location']['lat']::numeric as lat, 
		data['geometry']['location']['lng']::numeric as lng, 
		data['formatted_address']::varchar as address, 
		ST_SetSRID(ST_MakePoint(data['geometry']['location']['lng']::numeric, data['geometry']['location']['lat']::numeric), 4326) as location 
from house_search.raw_bakeries;

drop view if exists house_search.grocery_stores;
create view house_search.grocery_stores as 
select  data['name']::varchar as name, 
        data['place_id']::varchar as place_id,
		data['geometry']['location']['lat']::numeric as lat, 
		data['geometry']['location']['lng']::numeric as lng, 
		data['formatted_address']::varchar as address, 
		ST_SetSRID(ST_MakePoint(data['geometry']['location']['lng']::numeric, data['geometry']['location']['lat']::numeric), 4326) as location 
from house_search.raw_grocery_stores
where data['name']::varchar like '%ewel%' 
or data['name']::varchar like '%roger%' 
or data['name']::varchar like '%hole%ood%' 
or data['name']::varchar like '%ostco%' 
or data['name']::varchar like '%eijer%' 
or data['name']::varchar like '%rader%oe%';



drop view if exists house_search.hardware_stores;
create view house_search.hardware_stores as 
select  data['name']::varchar as name, 
        data['place_id']::varchar as place_id,
		data['geometry']['location']['lat']::numeric as lat, 
		data['geometry']['location']['lng']::numeric as lng, 
		data['formatted_address']::varchar as address, 
		ST_SetSRID(ST_MakePoint(data['geometry']['location']['lng']::numeric, data['geometry']['location']['lat']::numeric), 4326) as location 
from house_search.raw_hardware_stores;

drop view if exists house_search.home_improvement_stores;
create view house_search.home_improvement_stores as 
select  data['name']::varchar as name, 
        data['place_id']::varchar as place_id,
		data['geometry']['location']['lat']::numeric as lat, 
		data['geometry']['location']['lng']::numeric as lng, 
		data['formatted_address']::varchar as address, 
		ST_SetSRID(ST_MakePoint(data['geometry']['location']['lng']::numeric, data['geometry']['location']['lat']::numeric), 4326) as location 
from house_search.raw_home_improvement_stores
where 
(data['name']::varchar like '%Lowe%s%'
or data['name']::varchar like '%Menard%'
or data['name']::varchar like '%Home%Depot%') and (data['name']::varchar not like '%Pro%' and data['name']::varchar not like '%Garden%' and data['name']::varchar not like '%at The Home Depot%');




select a.house_number, a.location, b.place_id, b.location, a.location <-> b.location as distance from house_search.houses a join house_search.home_improvement_stores b on st_dwithin(a.location,b.location,.001) order by distance;
