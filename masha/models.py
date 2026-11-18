from django.db import models
from django.contrib.auth.models  import User
from datetime import datetime
#from channels.layers import get_channel_layer
from django.db.models.signals import pre_delete
from django.utils import timezone
from asgiref.sync import async_to_sync
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
import re

def image_uplod(instance,filename):

	   imagename,extension=filename.split(".")
	   return "jos/%s.%s"%(instance.title,extension)
class Safah(models.Model):
    name = models.TextField(blank=True)
    def __str__(self):
	 	   return  str(self.name)
class AStmrah(models.Model):
    name = models.TextField(blank=True)
    def __str__(self):
	 	   return  str(self.name)
class Vald_doc(models.Model):
    name = models.TextField(blank=True)
    def __str__(self):
	 	   return  str(self.name)
class Vald_tharb(models.Model):
    name = models.TextField(blank=True)
    def __str__(self):
	 	   return  str(self.name)
class  Mahfth(models.Model):
	 #user=models.OneToOneField(User,null=True, blank=True,on_delete=models.CASCADE)
	 name=models.CharField(max_length=300)
	 
	 def __str__(self):
	 	   return str(self.name)
class  Erea(models.Model):
	 #user=models.OneToOneField(User,null=True, blank=True,on_delete=models.CASCADE)
	 name=models.CharField(max_length=200)
	 mahfth=models.ForeignKey(Mahfth,null=True, blank=True,on_delete=models.CASCADE)

	 
	 def __str__(self):
	 	   return str(self.name)
class Eng_nazol(models.Model):

	 name=models.CharField(max_length=200)
	 
	 mahfth=models.ForeignKey(Mahfth,null=True, blank=True,on_delete=models.CASCADE)

	 class Meta: 

	 	permissions = (

            ("can_add_eng_nazol", "can_change_eng_nazol"),
        
        )
      

	 def __str__(self):
	    return str(self.name)

class  Gata(models.Model):
	 number=models.IntegerField( null=True)
	 name=models.CharField(max_length=300)
	 erea=models.ForeignKey(Erea,null=True, blank=True,on_delete=models.CASCADE)
	 def __str__(self):
	 	   return  str(self.name)
class Eng(models.Model):

	 name=models.CharField(max_length=200)
	 phone=models.CharField(max_length=200)
	 gata=models.ForeignKey(Gata,null=True, blank=True,on_delete=models.CASCADE)

	 class Meta: 

	 	permissions = (

            ("can_add_eng", "can_change_eng"),
        
        )
      

	 def __str__(self):
	    return str(self.name)
class  Unit(models.Model):
	 
	 name=models.CharField(max_length=200)
	 mahfth=models.ForeignKey(Mahfth,null=True, blank=True,on_delete=models.CASCADE)
	 class Meta: 

	 	permissions = (

            ("can_add_unit", "can_view_unit"),
        
        )
	 def __str__(self):
	 	   return str(self.id)
class Typ_bana(models.Model):
	 #user=models.OneToOneField(User,null=True, blank=True,on_delete=models.CASCADE)
	 number=models.IntegerField(primary_key=True,unique=True)
	 name=models.CharField(max_length=200)
	
	 
	 def __str__(self):
	 	   return str(self.name)
class Type_block(models.Model):
	 #user=models.OneToOneField(User,null=True, blank=True,on_delete=models.CASCADE)
	
	 name=models.CharField(max_length=200)
	 
	 def __str__(self):
	 	   return str(self.name)
class Type_natural(models.Model):
	 #user=models.OneToOneField(User,null=True, blank=True,on_delete=models.CASCADE)
	
	 name=models.CharField(max_length=200)
	 
	 def __str__(self):
	 	   return str(self.name)
class Type_seol(models.Model):
	 #user=models.OneToOneField(User,null=True, blank=True,on_delete=models.CASCADE)
	
	 name=models.CharField(max_length=200)
	 
	 def __str__(self):
	 	   return str(self.name)
class Type_kah(models.Model):
	 #user=models.OneToOneField(User,null=True, blank=True,on_delete=models.CASCADE)
	
	 name=models.CharField(max_length=200)
	 
	 def __str__(self):
	 	   return str(self.name)


 #user=models.OneToOneField(User,null=True, blank=True,on_delete=models.CASCADE)
	
	
class typ(models.Model):
	 #user=models.OneToOneField(User,null=True, blank=True,on_delete=models.CASCADE)
	 number=models.IntegerField(primary_key=True,unique=True)
	 name=models.CharField(max_length=200)
	 
	 def __str__(self):
	 	   return str(self.name)

class Type_map(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
	 	   return  str(self.id)
class Type_talb(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
	 	   return  str(self.id)
class Type_talb_astshr(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
	 	   return  str(self.id)


class Form(models.Model):
	 #user=models.OneToOneField(User,null=True, blank=True,on_delete=models.CASCADE)
	 type_block=models.ForeignKey( Type_block,null=True ,blank=True,on_delete=models.CASCADE)
	 type_natural=models.ForeignKey( Type_natural,null=True ,blank=True,on_delete=models.CASCADE)
	 type_seol=models.ForeignKey( Type_seol,null=True ,blank=True,on_delete=models.CASCADE)
	 type_kah=models.ForeignKey( Type_kah,null=True ,blank=True,on_delete=models.CASCADE)
	 type_talb_astshr=models.ForeignKey( Type_talb_astshr,null=True ,blank=True,on_delete=models.CASCADE)
	 kml_file = models.FileField(upload_to='kml_files/')
	 day=models.TextField(null=True)
	 safah=models.ForeignKey(Safah,null=True ,blank=True,on_delete=models.CASCADE)

	 
	
	 typ=models.ForeignKey(typ,null=True ,blank=True,on_delete=models.CASCADE)
	 day=models.TextField(null=True)
	 month=models.TextField(null=True)
	 mahfth=models.ForeignKey(Mahfth,null=True, blank=True,on_delete=models.CASCADE)
	 year=models.TextField(null=True)
	 ajaml=models.TextField(null=True)
	 sett=models.IntegerField(default=0,null=True)
	 streat_name_gr=models.TextField(null=True)
	 
	
	 unit=models.ForeignKey(Unit,null=True, blank=True,on_delete=models.CASCADE)
	
	 img_parsone=models.ImageField(upload_to='images/',null=True)
	 img_document=models.ImageField(upload_to='images/',null=True)
	 img_document_aqre=models.ImageField(upload_to='images/',null=True, blank=True)
	 name=models.CharField(max_length=200)
	 phone=models.TextField(null=True)
	 #type_card=models.ForeignKey(Type_card, blank=True,on_delete=models.CASCADE)
	 card_id=models.TextField(null=True)
	
	 typ_bana=models.ForeignKey(Typ_bana,null=True, blank=True,on_delete=models.CASCADE)
	 typ_aqur=models.CharField(max_length=200)
	
	 document_number=models.TextField(null=True,default=0)
	 erea_baser=models.TextField(null=True)
	 
	 digital =models.BooleanField(default=False,blank=False)
	 exit_eng =models.BooleanField(default=False,blank=False)
	 update =models.BooleanField(default=False,blank=False)
	 asher=models.TextField(null=True)
	 
	 show_form_nah=models.BooleanField(default=False,blank=False)
	 show_tasrah_karoj=models.BooleanField(default=False,blank=False)
	 agree_manger_rak=models.BooleanField(default=False,blank=False)
	 add_unit_motan_a=models.BooleanField(default=False,blank=False)
	
	
	 saft_sahb_talab=models.CharField(max_length=100)
	

	 streat_name=models.CharField(max_length=50) 
	 
	 account_qunit_fane=models.IntegerField(default=0,null=True)
	
	 content=models.CharField(max_length=100)
	 resone_refth=models.CharField(max_length=100)
	 name_wk=models.CharField(max_length=200)
	 phone_wk=models.TextField(default=0,blank=True)
	 hidden_ansh_hdm=models.TextField(default=0,blank=True)
	 card_id_wk=models.TextField(default=0,blank=True)
	 img_wkl=models.ImageField(upload_to='images/',null=True, blank=True)
	 broze=models.FloatField(blank=True,null=True)
	
	
	
	
	 masahi=models.BooleanField(default=False,blank=False)

	 return_fane_jmh=models.BooleanField(default=False,blank=False)
	 return_form=models.BooleanField(default=False,blank=False)
	
	 img_tlab_trkis=models.ImageField(upload_to='images/',null=True, blank=True)


	

	 tr_masah=models.BooleanField(default=False,blank=False)
	 return_masah_jm=models.BooleanField(default=False,blank=False)
	 tslem_rafth=models.BooleanField(default=False,blank=False)
	 tslem_astkmal=models.BooleanField(default=False,blank=False)


	
	 rafth_adarah_generl=models.BooleanField(default=False,blank=False)
	 sent_att = models.DateTimeField(auto_now_add=True, null=True, blank=True)
	 name_documnt=models.TextField(null=True)  
	 service_bana=models.CharField(max_length=400)
	 rafth_maml=models.BooleanField(default=False,blank=False)
	 talb_astkml =models.BooleanField(default=False,blank=False)
	 rasone_rafth_maml=models.TextField(blank=True)
	 erea_asqt=models.TextField(default=0,blank=True)
	 eng_nazol=models.TextField(default=0,blank=True)
	 width_street_big=models.TextField(null=True) 
	 width_street_big_not=models.FloatField(null=True,blank=True)  
	 opnin_eng=models.TextField(null=True)
	 
	

	
	 
	 
 
	 class Meta: 
	 	ordering=['-id'] 
	 	
	 	permissions = (

            ("can_add_form", "can_view_form"),
            ("can_change_form","can_delete_form"),
        )

	 def __str__(self):
	 	   return  str(self.id)
	 @property
	
	 def get_qunit(self):
	 	hasb=self.shift_form_hadod_set.all()
	 	total=0
	 	total_sum=0
	 	shm=0
	 	jn=0
	 	shr=0
	 	gr=0
	 	for item in hasb:
	 		if item.sh=="شمال":
	 			shm+=float(item.quantity)


	 		elif item.sh=="جنوب":
	 			jn+=float(item.quantity)
	 		elif item.sh=="شرق":
	 			shr+=float(item.quantity)
	 		elif item.sh=="غرب":
	 			gr+=float(item.quantity)


	 	total=((shm+jn)/2 )* ((shr+gr)/2)
	 	return total


	 @property
	 def get_qunit_f(self):
	 	hasb=self.shift_form_hadod_set.all()
	 	total=0
	 	for item in hasb:

	 		total+=float(item.quantity)

	 	return total
	 @property
	 def get_street(self):
	 	hasb=self.shift_form_hadod_set.all()
	 	total=0
	 	x=0
	 	y=0
	 	z=0
	 	m=0
	 	n=0
	 	for item in hasb:

	 		if item.sh=="شمال" and item.shar_atjah=="شارع":
	 			  x+=float(item.width_street)


	 		elif item.sh=="جنوب"  and item.shar_atjah=="شارع":
	 			y+=float(item.width_street)
	 		elif item.sh=="شرق"  and item.shar_atjah=="شارع":
	 			z+=float(item.width_street)

	 		elif item.sh=="غرب"  and item.shar_atjah=="شارع":
	 			m+=float(item.width_street)
	 	if x>=y and x>=z and x>=m:
	 		

	 		n=x//3
	 		return n
	 	elif y>=x and y>=z and y>=m:
	 		n=y//3
	 		return n
	 	elif z>=x and z>=y and z>=m :
	 		n=z//3
	 		return n
	 	elif m>=x and m>=y and m>=z :
	 		n=m//3
	 		return n
	 @property
	 def get_street_big(self):
	 	hasb=self.shift_form_hadod_set.all()
	 	total=0
	 	x=0
	 	y=0
	 	z=0
	 	m=0
	 	n=0
	 	for item in hasb:

	 		if item.sh=="شمال" and item.shar_atjah=="شارع":
	 			  x+=float(item.width_street)


	 		elif item.sh=="جنوب"  and item.shar_atjah=="شارع":
	 			y+=float(item.width_street)
	 		elif item.sh=="شرق"  and item.shar_atjah=="شارع":
	 			z+=float(item.width_street)

	 		elif item.sh=="غرب"  and item.shar_atjah=="شارع":
	 			m+=float(item.width_street)
	 	if x>=y and x>=z and x>=m:
	 		
	 		return x
	 	elif y>=x and y>=z and y>=m:
	 		
	 		return y
	 	elif z>=x and z>=y and z>=m :
	 	
	 		return z
	 	elif m>=x and m>=y and m>=z :
	 		
	 		return m



class Resone(models.Model):
	
	
	 name=models.CharField(max_length=100)
	 def __str__(self):
	 	   return str(self.name)
	 
class report_masahi(models.Model):
	#number=models.IntegerField(primary_key=True,unique=True,)
	mnsobe=models.TextField(default=0,blank=True)
	resone=models.ForeignKey(Resone,null=True, blank=True,on_delete=models.CASCADE)
	
	form=models.OneToOneField(Form,null=True, blank=True,on_delete=models.CASCADE)
	mahther_line=models.ImageField(upload_to='images/',null=True, blank=True)
	location=models.ImageField(upload_to='images/',null=True, blank=True)
	masahi=models.BooleanField(default=False,blank=False)
	masahi_convert=models.BooleanField(default=False,blank=False)
	convert_agin=models.BooleanField(default=False,blank=False)
	convert_agin_agree=models.BooleanField(default=False,blank=False)
	kml_file = models.FileField(upload_to='kml_files/')
	tr_masah=models.BooleanField(default=False,blank=False)
	name=models.TextField(default=0,blank=True)
	return_masah_jm=models.BooleanField(default=False,blank=False)
	opnine_eng=models.TextField(default=0,blank=True)
	ajaml=models.TextField(null=True)
	erea_asqt=models.TextField(default=0,blank=True)
	rafth_adarah_generl=models.BooleanField(default=False,blank=False)
	rafth_adarah_generl_by_manager_mahfth=models.BooleanField(default=False,blank=False)
	agree_adarah_generl_by_manager_mahfth=models.BooleanField(default=False,blank=False)
	print_nah=models.BooleanField(default=False,blank=False)
	resone_refth=models.TextField(default=0,blank=True)
	resone_refth_adrah=models.TextField(default=0,blank=True)
	type_map=models.ForeignKey(Type_map,null=True, blank=True,on_delete=models.CASCADE)
	
	def __str__(self):
	 	   return  str(self.name)
class Shift_form_hadod(models.Model):
	CURRENCY_CHOICES_L=[
	('', '---اختار الاتجاة---'),
	('شمال', 'شمال'),
	('جنوب', 'جنوب' ),
	('شرق', 'شرق'),
	('غرب', 'غرب'),] 
	CURRENCY_CHOICES_M=[
	  ('', '---اختار الجوار---'),
	  ('شارع', 'شارع'),
	  ('جار', 'جار '),
	  
	  ('م+جار', 'م+جار'),] 
	CURRENCY_CHOICES_T=[
	('', '---اختار نوع الشارع---'),
	('ترابي', 'ترابي'),
	('اسفلتي', 'اسفلتي  '),] 
	mahther_line=models.ImageField(upload_to='images/',null=True, blank=True)
	location=models.ImageField(upload_to='images/',null=True, blank=True)
	form=models.ForeignKey(Form,null=True, blank=True,on_delete=models.CASCADE)
	sh=models.TextField(default=0,blank=True, choices=CURRENCY_CHOICES_L)
	quantity=models.TextField(default=0,blank=True)
	shar_atjah=models.TextField(null=True,blank=True, choices=CURRENCY_CHOICES_M)
	true=models.CharField(max_length=15)
	width_street = models.PositiveIntegerField(null=True, blank=True )  # ✅ 
	type_street=models.TextField(null=True,blank=True,choices=CURRENCY_CHOICES_T)
	number_strate=models.CharField(max_length=15)
	agree_trh=models.BooleanField(default=False,blank=False)
	location=models.ImageField(upload_to='images/',null=True, blank=True)
	report_masahi=models.ForeignKey(report_masahi,null=True, blank=True,on_delete=models.CASCADE)
	class Meta: 
		permissions = (
			("can_add_shift_form_hadod", "can_view_shift_form_hadod"),)
	def __str__(self):
	 	   return  str(self.form)
# Create your models here.
class Mahther_line(models.Model):
	 eng_1=models.CharField(max_length=30)
	 eng_2=models.CharField(max_length=30)
	 eng_resive=models.CharField(max_length=30)
	 mahther_line_nah=models.ImageField(upload_to='images/',null=True, blank=True)
	 unit=models.ForeignKey(Unit,null=True, blank=True,on_delete=models.CASCADE)

	
	 class Meta: 
	 	ordering=['-id'] 
	 
	 	permissions = (

            ("can_add_mahther_line", "can_view_mahther_line"),
            ("can_change_mahther_line","can_delete_mahther_line"),        )
	 def __str__(self):
	 	   return  str(self.id)
class Streat(models.Model):
	
	 width_street=models.CharField(max_length=15)
	 type_street=models.CharField(max_length=15)
	 number_strate=models.CharField(max_length=15)
	 mahther_line=models.OneToOneField(Mahther_line,null=True, blank=True,on_delete=models.CASCADE)
	 def __str__(self):
	 	   return  str(self.id)

class Valdtion(models.Model):
	 verification_code=models.CharField(null=True, blank=True,max_length=6)
	 name=models.CharField(max_length=15)
	 massage=models.TextField(null=True)
	 phone=models.IntegerField(default=0,null=True)
	 def __str__(self):
	 	   return  str(self.verification_code)

class Conection(models.Model):
	 valdtion=models.OneToOneField(Valdtion,null=True, blank=True,on_delete=models.CASCADE)
	 red_bol=models.BooleanField(default=False,blank=False)
	
	 name=models.CharField(max_length=15)
	 massage=models.TextField(null=True)
	 red=models.TextField(null=True)
	 phone=models.IntegerField(default=0,null=True)
	
	 def __str__(self):
	 	   return  str(self.id)
class Shift_streatr(models.Model):
	CURRENCY_CHOICES_L=[
	('', '---اختار الاتجاة---'),
	('شمال', 'شمال'),
	('جنوب', 'جنوب' ),
	('شرق', 'شرق'),
	('غرب', 'غرب'),] 
	CURRENCY_CHOICES_M=[
	  ('', '---اختار الجوار---'),
	  ('شارع', 'شارع'),
	  ('جار', 'جار '),
	  ('شارع+جولة', 'شارع+جولة'),
	  ('م+جار', 'م+جار'),] 
	CURRENCY_CHOICES_T=[
	('', '---اختار نوع الشارع---'),
	('ترابي', 'ترابي'),
	('اسفلتي', 'اسفلتي  '),] 
	mahther_line=models.ForeignKey(Mahther_line,null=True, blank=True,on_delete=models.CASCADE)
	sh=models.TextField(default=0,blank=True,choices=CURRENCY_CHOICES_L)
	quantity=models.TextField(default=0,blank=True)
	shar_atjah=models.TextField(null=True,blank=True, choices=CURRENCY_CHOICES_M)
	true=models.CharField(max_length=15)
	width_street=models.CharField(max_length=15)
	type_street=models.TextField(null=True,blank=True, choices=CURRENCY_CHOICES_T)
	number_strate=models.CharField(max_length=15)



class Location(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    description = models.TextField(blank=True)
    form=models.OneToOneField(Form,null=True, blank=True,on_delete=models.CASCADE)

   
  

def validate_decimal(value):
	str_value = str(value)
	if str_value.startswith('-'):
	 str_value = str_value[1:]  # إزالة علامة السالب إذا كانت موجودة
	 if len(str_value.split('.')[0]) > 4:  # تحقق من الأرقام قبل الفاصلة
	 	raise ValidationError('يجب أن يحتوي الرقم على 4 أرقام كحد أقصى قبل الفاصلة العشرية.')

class Location_Utm(models.Model):
    utm_zone = models.TextField(blank=True)
    easting = models.IntegerField()
    northing =models.IntegerField()
    form=models.OneToOneField(Form,null=True, blank=True,on_delete=models.CASCADE)

    def __str__(self):
        return f"Zone: {self.utm_zone}, Easting: {self.easting}, Northing: {self.northing}"


	