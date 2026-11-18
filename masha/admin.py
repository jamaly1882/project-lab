from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Mahfth,Gata,Erea,Unit,Form,typ,Eng,Typ_bana,Shift_form_hadod,Streat,Mahther_line,Shift_streatr,Location,report_masahi,Conection,Location_Utm,Type_map,Valdtion,Type_block,Type_natural,Type_seol,Type_kah,Type_talb,Type_talb_astshr,AStmrah,Safah,Vald_doc,Vald_tharb,Eng_nazol,Resone
admin.site.register( Location_Utm)
admin.site.register( report_masahi)
admin.site.register( Type_map)
admin.site.register( Valdtion)


admin.site.register( Type_talb)

admin.site.register( Location)
admin.site.register( Shift_streatr)
admin.site.register( Mahther_line)
admin.site.register( Streat)
admin.site.register( Conection)
admin.site.register( Resone)

admin.site.register( Form)
admin.site.register( Typ_bana)
@admin.register(Type_natural)
class Type_naturalAdmin(ImportExportModelAdmin):
        pass
@admin.register(Type_kah)
class Type_kahAdmin(ImportExportModelAdmin):
        pass
@admin.register(Type_seol)
class Type_seolAdmin(ImportExportModelAdmin):
        pass

@admin.register(Type_block)
class Type_blockAdmin(ImportExportModelAdmin):
        pass
@admin.register(Eng_nazol)
class Eng_nazolAdmin(ImportExportModelAdmin):
        pass
@admin.register(Type_talb_astshr)
class Type_talb_astshrAdmin(ImportExportModelAdmin):
        pass

admin.site.register(Shift_form_hadod)
@admin.register(typ)
class typAdmin(ImportExportModelAdmin):
        pass
# Register your models here.
@admin.register(Mahfth)
class MahfthAdmin(ImportExportModelAdmin):
        pass
@admin.register(Erea)
class EreaAdmin(ImportExportModelAdmin):
        pass
@admin.register(Gata)
class GataAdmin(ImportExportModelAdmin):
        pass
@admin.register(Eng)
class EngAdmin(ImportExportModelAdmin):
        pass
@admin.register(Unit)
class UnitAdmin(ImportExportModelAdmin):
        pass
@admin.register(Safah)
class SafahAdmin(ImportExportModelAdmin):
        pass
@admin.register(AStmrah)
class AStmrahAdmin(ImportExportModelAdmin):
        pass

@admin.register(Vald_tharb)
class Vald_tharbAdmin(ImportExportModelAdmin):
        pass

@admin.register(Vald_doc)
class Vald_docAdmin(ImportExportModelAdmin):
        pass

