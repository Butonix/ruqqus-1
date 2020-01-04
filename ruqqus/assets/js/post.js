function post(url, callback, errortext) {
  var xhr = new XMLHttpRequest();
  xhr.open("POST", url, true);
  var form = new FormData()
  form.append("formkey", "{{ v.formkey }}");
  xhr.withCredentials=true;
  xhr.onload=callback
  xhr.onerror=function(){alert(errortext)}
  xhr.send(form);
}