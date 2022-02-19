var pos_xmlhttp;

function sushi_random()
{
    var rn;

    rn = Math.floor(Math.random()*100001);
    return '&randn='+rn;
}


function requestObject()
{
  var xmlhttp;
  if (window.XMLHttpRequest)
  {
    // code for IE7+, Firefox, Chrome, Opera, Safari
    xmlhttp=new XMLHttpRequest();
  } else
  {
    // code for IE6, IE5
    xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
  }

  return xmlhttp;
}

function sushi_process_common(type, aa)
{
    if (type == 'redirect')
    {
      var where = aa['where'];
      where = where.replace(/\%26/g,'&');
      window.location.href = where;

    } else if (type == 'refill')
    {
      var where = aa['where'];
      var what  = aa['what'];
      var where_html = document.getElementById(where);

      if (where_html != null)
      {
        where_html.innerHTML = what;
      }

    } else if (type == 'append')
    {
      var where = aa['where'];
      var what  = aa['what'];
      var where_html = document.getElementById(where);

      if (where_html != null)
      {
        where_html.innerHTML = where_html.innerHTML + what;
      }

    }
}

function pos_response()
{
  var content;
  var res;
  var e;

  if (pos_xmlhttp.readyState == 4)
  {
    res = pos_xmlhttp.responseText;

    pos_process_extend(res);

    e = document.getElementById('ins');

    if (e != null)
    {
      pos_local_clr();
      pos_refresh();
    }
  }
}

function pos_response_norefresh()
{
  var content;
  var res;
  var e;

  if (pos_xmlhttp.readyState == 4)
  {
    res = pos_xmlhttp.responseJSON;

    pos_process_extend(res);

    e = document.getElementById('ins');


    if (e != null)
    {
      pos_local_clr();
    }
  }
}

function pos_process_extend(response)
{
  var aa;


  aa = JSON.parse(response)

  for(var i = 0, len = aa.length; i < len; i += 1)
  {
    var type = aa[i]['type'];

    if (type == 'total')
    {
      var total = aa[i]['total'];
      setTotal = total;

    } else if (type == 'reset')
    {
	setReset = 1;

    } else
    {
      sushi_process_common(type, aa[i]);
    }
  }
}

function pos_refresh()
{
    var e,t,s;
    var x, h;
    s = document.getElementById('lstate1');

    h='';

    if (setRefund == 4)
    {
	h='Refund ';
    }

    if (setNum != 1)
    {
	h = h+'x '+setNum;
    }

    if (h == '')
    {
	h = '&nbsp;';
    }

    s.innerHTML = h;

    s = document.getElementById('lstate2');

    if (setShiftId != 0)
    {
      s.innerHTML = setShiftLabel;
    } else
    {
      s.innerHTML = '&nbsp;';
    }


    s = document.getElementById('rstate2');

    if (setTotal < 0)
    {
      s.innerHTML = 'Total -&pound;'+Number(setTotal/-100).toFixed(2);
    } else
    {
      s.innerHTML = 'Total &pound;'+Number(setTotal/100).toFixed(2);
    }

    e = document.getElementById('ins');
    t = document.getElementById('target');
    t.scrollTop = t.scrollHeight;
    e.focus();
}

function get_radio_value(radio)
{
  var rs = document.getElementsByName(radio);

  for (var i = 0, length = rs.length; i < length; i++)
  {
    if (rs[i].checked)
    {
      return rs[i].value;
    }
  }
  return '';
}

// action commands

encodeURIComponent

function command_login()
{

    username = encodeURIComponent(document.getElementById('ofUser').value);
    password = encodeURIComponent(document.getElementById('ofPassword').value);

    pos_xmlhttp = requestObject();
    pos_xmlhttp.onreadystatechange=pos_response;
    pos_xmlhttp.open('GET','/action?command=login&usernameinput='+username+'&passwordinput='+password+sushi_random(),true);
    pos_xmlhttp.send(null);
}

function command_add()
{
    loc = encodeURIComponent(document.getElementById('ofLocation').value);
    type = encodeURIComponent(get_radio_value('ofType'));
    occupancy = encodeURIComponent(get_radio_value('ofOccupancy'));

    pos_xmlhttp = requestObject();
    pos_xmlhttp.onreadystatechange=pos_response;
    pos_xmlhttp.open('GET','/action?command=add&locationinput='+loc+'&occupancyinput='+occupancy+'&typeinput='+type+sushi_random(),true);
    pos_xmlhttp.send(null);
}

function command_undo()
{

    loc = encodeURIComponent(document.getElementById('ofLocation').value);
    type = encodeURIComponent(get_radio_value('ofType'));
    occupancy = encodeURIComponent(get_radio_value('ofOccupancy'));

    pos_xmlhttp = requestObject();
    pos_xmlhttp.onreadystatechange=pos_response;
    pos_xmlhttp.open('GET','/action?command=undo&locationinput='+loc+'&occupancyinput='+occupancy+'&typeinput='+type+sushi_random(),true);
    pos_xmlhttp.send(null);
}

function command_back()
{
    pos_xmlhttp = requestObject();
    pos_xmlhttp.onreadystatechange=pos_response;
    pos_xmlhttp.open('GET','/action?command=back'+sushi_random(),true);
    pos_xmlhttp.send(null);
}

function command_summary()
{
    pos_xmlhttp = requestObject();
    pos_xmlhttp.onreadystatechange=pos_response;
    pos_xmlhttp.open('GET','/action?command=summary'+sushi_random(),true);
    pos_xmlhttp.send(null);
}

function command_logout()
{
    pos_xmlhttp = requestObject();
    pos_xmlhttp.onreadystatechange=pos_response;
    pos_xmlhttp.open('GET','/action?command=logout'+sushi_random(),true);
    pos_xmlhttp.send(null);
}

