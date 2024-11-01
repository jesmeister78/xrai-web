delete from procedures;

INSERT INTO public.procedures(
	id, user_id, patient_name, ur_identifier, date, hospital, 
	surgeon, surgery_type, indication, default_img_src)
	--VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
	select 
		gen_random_uuid()
		
		, u.id
		, 'John Smith'
		, 'UR1234'
		, '2024-10-02'
		, 'Epworth'
		, 'Mr Surgeon'
		, '1'
		, '2'
		, ''
from users u
where u.username = 'jes';

insert into procedures(
	id, user_id, patient_name, ur_identifier, date, hospital, surgeon, surgery_type, indication, default_img_src)
	--VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
	select 
		gen_random_uuid()
	
		, u.id
		, 'Jane Smith'
		, 'UR5678'
		, '2024-10-01'
		, 'Epworth'
		, 'Mrs Surgeon'
		, '2'
		, '3'
		, ''
from users u
where u.username = 'jes';

insert into procedures(
	id, user_id, patient_name, ur_identifier, date, hospital, surgeon, surgery_type, indication, default_img_src)
	--VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
	select 
		gen_random_uuid()
	
		, u.id
		, 'Magda Kavorkian'
		, 'UR9876'
		, '2024-10-03'
		, 'Epworth'
		, 'Mrs Surgeon'
		, '1'
		, '4'
		, ''
from users u
where u.username = 'jes';

select * from procedures;

