insert into users
select
	gen_random_uuid(),
	'jes',
	'jesmeister@live.com'


select  * 
from users
fetch first 10 rows only