
  var $j = jQuery.noConflict();

 $j(document).ready(function() {

    $('#form_a').submit(function(e) {
        e.preventDefault();
        
  
        var phone = $('#phone').val();
         var name_aml = $('#name_aml').val();
           var card_id = $('#card_id').val();
           var erea_11 = $('#erea_11').val();
           var hid_ansh_hdm=$('#hid_ansh_hdm').val();
           var hid_type_form_rakash=$('#hid_type_form_rakash').val();
           var hid_type_document=$('#hid_type_document').val();
            var hid_type_aqure=$('#hid_type_aqure').val();
            var streat_name=$('#streat_name').val();
            var img_parson_card=$('#img_parson_card').val();
            var img_document_baser_nah=$('#img_document_baser_nah').val();

          if (hid_ansh_hdm.length=="") {
            alert('يرجى تحديد الغرض من التقرير');  
            return false;
        }
        else if (hid_type_form_rakash.length=="") {
            alert('يرجى تحديد صفة مقدم الطلب');
            return false;
        }
         
        else if (name_aml.length=="") {
            alert('يرجى ادخال الاسم');document.getElementById("phone").focus();

            return false;
        }
     

         
        else if (phone.length=="") {
            alert('يرجى ادحال رقم هاتم');document.getElementById("phone").focus();

            return false;
        }
      
             else   if (phone.length <0){
               alert('لايمكنك ادخال نص');

            return false;
               
          }
        else   if (phone.length <9){
               alert('رقم الهاتف اصغر من 9');

            return false;
               
          }
       else  if (card_id.length =="") {
            alert('يرجى تجديد رقم الهوية');

            return false;
        }
        else  if (card_id.length <5) {
            alert('يرجى تحديد رقم هوية صالحة');

            return false;
        }

         else  if (hid_type_document.length =="") {
            alert('يرجى تحديد نوع وثيقة الملكية');

            return false;
        }
           else  if (erea_11.length =="") {
            alert('ادخل مساحة الوثيقة');

            return false;
        }
   
        else  if (hid_type_aqure.length =="") {
            alert('تحقق من صحة الوثيقة');

            return false;
        }
        else  if (streat_name.length =="") {
            alert('ادخل اسم الحي');

            return false;
        }

 


else{

var data = {
  'name_aml': document.querySelector('#name_aml').value,
    'phone': document.querySelector('#phone').value,
    'card_id': document.querySelector('#card_id').value,
    'erea_11': document.querySelector('#erea_11').value,
    'hid_type_form_rakash': document.querySelector('#hid_type_form_rakash').value,
    'hid_type_document': document.querySelector('#hid_type_document').value,
     'hid_type_aqure': document.querySelector('#hid_type_aqure').value,
      'streat_name': document.querySelector('#streat_name').value,

 'text_36': document.querySelector('#text36').value,
  'hid_ansh_hdm': document.querySelector('#hid_ansh_hdm').value,
    'day': document.querySelector('#day').value,
     'month': document.querySelector('#month').value,
   'year': document.querySelector('#year').value,
   'number_dcoum_in_t': document.querySelector('#number_dcoum_in_t').value,
   'f2': document.querySelector('#f2').value,
      'f4': document.querySelector('#f4').value,
         'f6': document.querySelector('#f6').value,




};
const jsonData = JSON.stringify(data);


fetch('http://127.0.0.1:8000/my_job/form_add_by_html_page', {
  method: 'POST',

 

      headers:{'Content-Type':'application/json','X-CSRFToken':csrftoken,},

  
  body:  jsonData

})
.then(response => {
  // القيام بشيء بعد الاستجابة من Django
})
.catch(error => {
  // القيام بشيء في حالة وجود خطأ
})
}
});
});






</script>