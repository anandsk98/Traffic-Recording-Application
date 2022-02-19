 #!/usr/bin/env python

# This is a simple web server for a traffic counting application.
# It's your job to extend it by adding the backend functionality to support
# recording the traffic in a SQL database. You will also need to support
# some predefined users and access/session control. You should only
# need to extend this file. The client side code (html, javascript and css)
# is complete and does not require editing or detailed understanding.

# import the various libraries needed
import http.cookies as Cookie # some cookie handling support
from http.server import BaseHTTPRequestHandler, HTTPServer # the heavy lifting of the web server
import urllib # some url parsing support
import json # support for json encoding
import sys # needed for agument handling

import sqlite3
import time
import datetime
from dateutil.relativedelta import relativedelta


def access_database(dbfile, query):
    connect = sqlite3.connect(dbfile)
    cursor = connect.cursor()
    cursor.execute(query)
    connect.commit()
    connect.close()

def access_database_with_result(dbfile, query):
    connect = sqlite3.connect(dbfile)
    cursor = connect.cursor()
    rows = cursor.execute(query).fetchall()
    connect.commit()
    connect.close()
    return rows

database = 'traffic.db'

def check_log(iuser, imagic):
    start= access_database_with_result(database,"SELECT start FROM session,users WHERE session.userid=users.userid and username='{}' and magic='{}'".format(iuser, imagic))
    maxx= access_database_with_result(database,"SELECT MAX(start) FROM session,users WHERE session.userid=users.userid and username='{}'".format(iuser))
    if(len(start) == 0):
        return False
    else:
        if(start[0][0] == maxx[0][0]):
            return True
        else:
            return False

def build_response_refill(where, what):
    """This function builds a refill action that allows part of the
       currently loaded page to be replaced."""
    return {"type":"refill","where":where,"what":what}


def build_response_redirect(where):
    """This function builds the page redirection action
       It indicates which page the client should fetch.
       If this action is used, only one instance of it should
       contained in the response and there should be no refill action."""
    return {"type":"redirect", "where":where}


def handle_validate(iuser, imagic):
    """Decide if the combination of user and magic is valid"""
    ## alter as required
    
    row = access_database_with_result(database,"SELECT * FROM session,users WHERE session.userid=users.userid and username='{}' and   magic='{}' and end=0".format(iuser, imagic))
    if(len(row) > 0):
        return True
    else:
        return False


def handle_delete_session(iuser, imagic):
    """Remove the combination of user and magic from the data base, ending the login"""
    now = int(time.time())
    userid = access_database_with_result(database,"SELECT users.userid FROM users,session WHERE session.userid=users.userid and username='{}' and magic='{}'".format(iuser, imagic))
    access_database(database,"UPDATE session SET end={} WHERE userid={} and magic='{}'".format(now,userid[0][0], imagic))
    return

def handle_login_request(iuser, imagic, parameters):
    """A user has supplied a username (parameters['usernameinput'][0])  
       and password (parameters['passwordinput'][0]) check if these are
       valid and if so, create a suitable session record in the database
       with a random magic identifier that is returned.
       Return the username, magic identifier and the response action set."""

    response = []
    if(len(parameters) == 4):
        if(isinstance(parameters['usernameinput'][0],str) and isinstance(parameters['passwordinput'][0],str)):
            #encrypted = hashlib.sha256(parameters['passwordinput'][0].encode('utf-8')).hexdigest()
            encrypted = parameters['passwordinput'][0]
            if handle_validate(iuser, imagic) == True:
                    handle_delete_session(iuser, imagic)
                
                # else:
                #     handle_delete_session(iuser, imagic)

            response = []
            ## alter as required
            user = parameters['usernameinput'][0]
            #magic = str(random.randrange(1000000000,9999999999))
            magic = str(parameters['randn'][0])
            userid = access_database_with_result(database,"SELECT userid FROM users WHERE username='{}'".format(user))
            if(len(userid) == 0):
                response.append(build_response_refill('message', 'No username found'))
                user = '!'
                magic = ''
                return [user, magic, response]
                # access_database(database,"INSERT INTO users(username,password) VALUES ('{}','{}')".format(user,encrypted))
                # userid=access_database_with_result(database,"SELECT userid FROM users WHERE username='{}' and password='{}'".format(user,encrypted))
            else:
                userid = access_database_with_result(database,"SELECT userid FROM users WHERE username='{}' and password='{}'".format(user, encrypted))
                if(len(userid) == 0):
                    response.append(build_response_refill('message', 'Invalid password'))
                    user = '!'
                    magic = ''
                    return [user, magic, response]
        
            now = int(time.time())

            access_database(database,"INSERT INTO session(userid,magic,start,end) VALUES ({},'{}',{},0)".format(userid[0][0], magic, now))
            response.append(build_response_redirect('/page.html'))
            
        else: ## The user is not valid  
            response.append(build_response_refill('message', 'Invalid username or password'))
            user = '!'
            magic = ''
    else:
        response.append(build_response_refill('message', 'No username or password given'))
        user = '!'
        magic = ''

    return [user, magic, response]


def handle_add_request(iuser, imagic, parameters):
    """The user has requested a vehicle be added to the count
       parameters['locationinput'][0] the location to be recorded
       parameters['occupancyinput'][0] the occupant count to be recorded
       parameters['typeinput'][0] the type to be recorded
       Return the username, magic identifier (these can be empty  strings) and the response action set."""
    response = []
    ## alter as required
    if handle_validate(iuser, imagic) != True:
        #Invalid sessions redirect to login
        ###do later
        response.append(build_response_redirect('/index.html'))
        response.append(build_response_refill('message', 'Not logged in.'))
        response.append(build_response_refill('total', '0'))
        user = '!'
        magic = ''
    else: ## a valid session so process the addition of the entry.
        
        x = check_log(iuser,imagic)
        if(x == False):
            user = '!'
            magic = ''
            response.append(build_response_redirect('/index.html'))
        else:
            if(len(parameters) != 5):
                user = iuser
                magic = imagic
                sessionid = access_database_with_result(database,"SELECT sessionid FROM session,users WHERE session.userid=users.userid and username='{}' and magic='{}'".format(iuser,imagic))
                total = len(access_database_with_result(database,"SELECT * from traffic WHERE sessionid={}".format(sessionid[0][0])))
                response.append(build_response_refill('message', 'No location given.'))
                response.append(build_response_refill('total', str(total)))
            else:
                user = iuser
                magic = imagic
                now = int(time.time())

                # if(parameters['occupancyinput'][0] in [1,2,3,4]):
                #     response.append(build_response_refill('message', 'Invalid occupancy'))
                #     return [user, magic, response]

                if(parameters['occupancyinput'][0] not in ['1','2','3','4']):
                    sessionid = access_database_with_result(database,"SELECT sessionid FROM session,users WHERE session.userid=users.userid and username='{}' and magic='{}'".format(iuser,imagic))
                    total = len(access_database_with_result(database,"SELECT * from traffic WHERE sessionid={}".format(sessionid[0][0])))
                    response.append(build_response_refill('message', 'Invalid occupancy'))
                    response.append(build_response_refill('total', str(total)))
                    return [user, magic, response]
                    
                if(parameters['typeinput'][0] == 'car'):
                    typ = 0
                elif(parameters['typeinput'][0] == 'van'):
                    typ = 1
                elif(parameters['typeinput'][0] == 'truck'):
                    typ = 2
                elif(parameters['typeinput'][0] == 'taxi'):
                    typ = 3
                elif(parameters['typeinput'][0] == 'other'):
                    typ = 4
                elif(parameters['typeinput'][0] == 'motorbike'):
                    typ = 5
                elif(parameters['typeinput'][0] == 'bicycle'):
                    typ = 6
                elif(parameters['typeinput'][0] == 'bus'):
                    typ = 7
                else:
                    response.append(build_response_refill('message', 'Invalid vehicle'))
                    return [user, magic, response]

                sessionid = access_database_with_result(database,"SELECT sessionid FROM session,users WHERE session.userid=users.userid and username='{}' and magic='{}'".format(iuser,imagic))

                access_database(database,"INSERT INTO traffic(sessionid,time,type,occupancy,location,mode) VALUES ({},{},{},{},'{}',{})".format(sessionid[0][0],now,typ,parameters['occupancyinput'][0],parameters['locationinput'][0],1))


                total = len(access_database_with_result(database,"SELECT * from traffic WHERE sessionid={}".format(sessionid[0][0])))
                response.append(build_response_refill('message', 'Entry added.'))
                response.append(build_response_refill('total', str(total)))
                
    return [user, magic, response]


def handle_undo_request(iuser, imagic, parameters):
    """The user has requested a vehicle be removed from the count
       This is intended to allow counters to correct errors.
       parameters['locationinput'][0] the location to be recorded
       parameters['occupancyinput'][0] the occupant count to be recorded
       parameters['typeinput'][0] the type to be recorded
       Return the username, magic identifier (these can be empty  strings) and the response action set."""
    response = []
    ## alter as required
    if handle_validate(iuser, imagic) != True:
        #Invalid sessions redirect to login
        response.append(build_response_redirect('/index.html'))
        response.append(build_response_refill('message', 'Not logged in.'))
        response.append(build_response_refill('total', 0))
        user = '!'
        magic = ''
    else: ## a valid session so process the recording of the entry.
        x = check_log(iuser,imagic)
        if(x == False):
            user = '!'
            magic = ''
            response.append(build_response_redirect('/index.html'))
        else:
            if(len(parameters) != 5):

                user = iuser
                magic = imagic
                sessionid = access_database_with_result(database,"SELECT sessionid FROM session,users WHERE session.userid=users.userid and username='{}' and magic='{}'".format(iuser,imagic))
                total = len(access_database_with_result(database,"SELECT * from traffic WHERE sessionid={} and mode=1".format(sessionid[0][0])))
                response.append(build_response_refill('message', 'No location given.'))
                response.append(build_response_refill('total', str(total)))
            else:
                user = iuser
                magic = imagic
                now = int(time.time())

                if(parameters['occupancyinput'][0] not in ['1','2','3','4']):
                    response.append(build_response_refill('message', 'Invalid occupancy'))
                    return [user, magic, response]

                if(parameters['typeinput'][0] == 'car'):
                    typ = 0
                elif(parameters['typeinput'][0] == 'van'):
                    typ = 1
                elif(parameters['typeinput'][0] == 'truck'):
                    typ = 2
                elif(parameters['typeinput'][0] == 'taxi'):
                    typ = 3
                elif(parameters['typeinput'][0] == 'other'):
                    typ = 4
                elif(parameters['typeinput'][0] == 'motorbike'):
                    typ = 5
                elif(parameters['typeinput'][0] == 'bicycle'):
                    typ = 6
                elif(parameters['typeinput'][0] == 'bus'):
                    typ = 7
                else:
                    response.append(build_response_refill('message', 'Invalid vehicle'))
                    return [user, magic, response]

                sessionid = access_database_with_result(database,"SELECT sessionid FROM session,users WHERE session.userid=users.userid and username='{}' and magic='{}'".format(iuser,imagic))

                access_database(database,"UPDATE traffic SET mode=2 WHERE recordid=(SELECT recordid FROM traffic WHERE sessionid={} and location='{}' and occupancy={} and type={} and mode=1 ORDER BY time DESC LIMIT 1)".format(sessionid[0][0],parameters['locationinput'][0],parameters['occupancyinput'][0],typ))
                access_database(database,"INSERT INTO traffic(sessionid,time,type,occupancy,location,mode) VALUES ({},{},{},{},'{}',{})".format(sessionid[0][0],now,typ,parameters['occupancyinput'][0],parameters['locationinput'][0],0))

                total = len(access_database_with_result(database,"SELECT * from traffic WHERE sessionid={} and mode=1".format(sessionid[0][0])))

                response.append(build_response_refill('message', 'Entry Un-done.'))
                response.append(build_response_refill('total', str(total)))

    return [user, magic, response]


def handle_back_request(iuser, imagic, parameters):
    """This code handles the selection of the back button on the record form (page.html)
       You will only need to modify this code if you make changes elsewhere that break its behaviour"""
    response = []
    ## alter as required
    x = check_log(iuser, imagic)
    if(x == False):
        user = '!'
        magic = ''
        response.append(build_response_redirect('/index.html'))
    else:
        if handle_validate(iuser, imagic) != True:
            response.append(build_response_redirect('/index.html'))
        else:
            response.append(build_response_redirect('/summary.html'))
    user = ''
    magic = ''
    return [user, magic, response]


def handle_logout_request(iuser, imagic, parameters):
    """This code handles the selection of the logout button on the summary page (summary.html)
       You will need to ensure the end of the session is recorded in the database
       And that the session magic is revoked."""
    ###check parameters
    response = []
    ## alter as required
    x = check_log(iuser,imagic)
    if(x == False):
        user = '!'
        magic = ''
        response.append(build_response_redirect('/index.html'))
    else:
        now = int(time.time())
        if(iuser != '!'):
            userid = access_database_with_result(database,"SELECT users.userid FROM users,session WHERE session.userid=users.userid and username='{}' and magic='{}'".format(iuser,imagic))
            access_database(database,"UPDATE session SET end={} WHERE userid={} and magic='{}'".format(now,userid[0][0],imagic))
        response.append(build_response_redirect('/index.html'))
        user = '!'
        magic = ''
    return [user, magic, response]


def handle_summary_request(iuser, imagic, parameters):
    """This code handles a request for an update to the session summary values.
       You will need to extract this information from the database.
       You must return a value for all vehicle types, even when it's zero."""
    response = []
    ## alter as required
    if handle_validate(iuser, imagic) != True:
        user = '!'
        magic = ''
        response.append(build_response_redirect('/index.html'))
    else:
        x = check_log(iuser,imagic)
        if(x == False):
            user = '!'
            magic = ''
            response.append(build_response_redirect('/index.html'))
        else:
            sessionid = access_database_with_result(database,"SELECT sessionid FROM session,users WHERE session.userid=users.userid and username='{}' and magic='{}'".format(iuser,imagic))
            typ = access_database_with_result(database,"SELECT type FROM traffic WHERE sessionid={} and mode=1".format(sessionid[0][0]))
            sum_car = 0
            sum_van = 0
            sum_truck = 0
            sum_taxi = 0
            sum_other = 0
            sum_motor = 0
            sum_cycle = 0
            sum_bus = 0
            for i in typ:
                if(i[0] == 0):
                    sum_car += 1
                elif(i[0] == 1):
                    sum_van += 1
                elif(i[0] == 2):
                    sum_truck += 1
                elif(i[0] == 3):
                    sum_taxi += 1
                elif(i[0] == 4):
                    sum_other += 1
                elif(i[0] == 5):
                    sum_motor += 1
                elif(i[0] == 6):
                    sum_cycle += 1
                elif(i[0] == 7):
                    sum_bus += 1
            total= sum_car + sum_van + sum_truck + sum_taxi + sum_other + sum_motor + sum_cycle + sum_bus
            response.append(build_response_refill('sum_car', str(sum_car)))
            response.append(build_response_refill('sum_taxi', str(sum_taxi)))
            response.append(build_response_refill('sum_bus', str(sum_bus)))
            response.append(build_response_refill('sum_motorbike', str(sum_motor)))
            response.append(build_response_refill('sum_bicycle', str(sum_cycle)))
            response.append(build_response_refill('sum_van', str(sum_van)))
            response.append(build_response_refill('sum_truck', str(sum_truck)))
            response.append(build_response_refill('sum_other', str(sum_other)))
            response.append(build_response_refill('total',str(total)))
            user = ''
            magic = ''
    return [user, magic, response]


# HTTPRequestHandler class
class myHTTPServer_RequestHandler(BaseHTTPRequestHandler):

    # GET This function responds to GET requests to the web server.
    def do_GET(self):

        # The set_cookies function adds/updates two cookies returned with a webpage.
        # These identify the user who is logged in. The first parameter identifies the user
        # and the second should be used to verify the login session.
        def set_cookies(x, user, magic):
            ucookie = Cookie.SimpleCookie()
            ucookie['u_cookie'] = user
            x.send_header("Set-Cookie", ucookie.output(header='', sep=''))
            mcookie = Cookie.SimpleCookie()
            mcookie['m_cookie'] = magic
            x.send_header("Set-Cookie", mcookie.output(header='', sep=''))

        # The get_cookies function returns the values of the user and magic cookies if they exist
        # it returns empty strings if they do not.
        def get_cookies(source):
            rcookies = Cookie.SimpleCookie(source.headers.get('Cookie'))
            user = ''
            magic = ''
            for keyc, valuec in rcookies.items():
                if keyc == 'u_cookie':
                    user = valuec.value
                if keyc == 'm_cookie':
                    magic = valuec.value
            return [user, magic]

        # Fetch the cookies that arrived with the GET request
        # The identify the user session.
        user_magic = get_cookies(self)

        print(user_magic)

        # Parse the GET request to identify the file requested and the parameters
        parsed_path = urllib.parse.urlparse(self.path)

        # Decided what to do based on the file requested.

        # Return a CSS (Cascading Style Sheet) file.
        # These tell the web client how the page should appear.
        if self.path.startswith('/css'):
            self.send_response(200)
            self.send_header('Content-type', 'text/css')
            self.end_headers()
            with open('.'+self.path, 'rb') as file:
                self.wfile.write(file.read())
            file.close()

        # Return a Javascript file.
        # These tell contain code that the web client can execute.
        elif self.path.startswith('/js'):
            self.send_response(200)
            self.send_header('Content-type', 'text/js')
            self.end_headers()
            with open('.'+self.path, 'rb') as file:
                self.wfile.write(file.read())
            file.close()

        # A special case of '/' means return the index.html (homepage)
        # of a website
        elif parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('./index.html', 'rb') as file:
                self.wfile.write(file.read())
            file.close()

        # Return html pages.
        elif parsed_path.path.endswith('.html'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            with open('.'+parsed_path.path, 'rb') as file:
                self.wfile.write(file.read())
            file.close()

        # The special file 'action' is not a real file, it indicates an action
        # we wish the server to execute.
        elif parsed_path.path == '/action':
            self.send_response(200) #respond that this is a valid page request
            # extract the parameters from the GET request.
            # These are passed to the handlers.
            parameters = urllib.parse.parse_qs(parsed_path.query)

            if 'command' in parameters:
                # check if one of the parameters was 'command'
                # If it is, identify which command and call the appropriate handler function.
                if parameters['command'][0] == 'login':
                    [user, magic, response] = handle_login_request(user_magic[0], user_magic[1], parameters)
                    #The result of a login attempt will be to set the cookies to identify the session.
                    set_cookies(self, user, magic)
                elif parameters['command'][0] == 'add':
                    [user, magic, response] = handle_add_request(user_magic[0], user_magic[1], parameters)
                    if user == '!': # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')
                elif parameters['command'][0] == 'undo':
                    [user, magic, response] = handle_undo_request(user_magic[0], user_magic[1], parameters)
                    if user == '!': # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')
                elif parameters['command'][0] == 'back':
                    [user, magic, response] = handle_back_request(user_magic[0], user_magic[1], parameters)
                    if user == '!': # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')
                elif parameters['command'][0] == 'summary':
                    [user, magic, response] = handle_summary_request(user_magic[0], user_magic[1], parameters)
                    if user == '!': # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')
                elif parameters['command'][0] == 'logout':
                    [user, magic, response] = handle_logout_request(user_magic[0], user_magic[1], parameters)
                    if user == '!': # Check if we've been tasked with discarding the cookies.
                        set_cookies(self, '', '')
                else:
                    # The command was not recognised, report that to the user.
                    response = []
                    response.append(build_response_refill('message', 'Internal Error: Command not recognised.'))

            else:
                # There was no command present, report that to the user.
                response = []
                response.append(build_response_refill('message', 'Internal Error: Command not found.'))

            text = json.dumps(response)
            print(text)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(bytes(text, 'utf-8'))

        elif self.path.endswith('/statistics/hours.csv'):
            ## if we get here, the user is looking for a statistics file
            ## this is where requests for /statistics/hours.csv should be handled.
            ## you should check a valid user is logged in. You are encouraged to wrap this behavour in a function.

            u = access_database_with_result(database,"SELECT username,start,MAX(end) from session,users WHERE session.userid=users.userid GROUP BY username")

            v = access_database_with_result(database,"SELECT username from users")
            uv=[]
            for i in v:
                flag=0
                for j in u:
                    if(i[0]==j[0]):
                        flag=1
                        k=j[1]
                        l=j[2]

                if(flag==1):
                    uv.append((i[0],k,l))
                else:
                    uv.append((i[0],0,0))
            
            last = access_database_with_result(database,"SELECT MAX(end) from session")
            users = []
            # username, start timestamp,logout timestamp, logout start of day timestamp
            for i in uv:
                if(i[2] == 0):
                    logout_day = 0
                    logout_week = 0
                    logout_month = 0
                else:
                    logout_day = datetime.datetime.fromtimestamp(last[0][0])
                    l = logout_day
                    year = int(logout_day.strftime('%Y'))
                    month = int(logout_day.strftime('%m'))
                    day = int(logout_day.strftime('%d'))
                    logout_day = int(datetime.datetime(year,month,day,0,0).timestamp())

                    logout_week = logout_day-518400

                    # logout_month=l.replace( month=month-1)
                    # year=int(logout_month.strftime('%Y'))
                    # month=int(logout_month.strftime('%m'))
                    # day=int(logout_month.strftime('%d'))
                    # logout_month=int(datetime.datetime(year,month,day,0,0).timestamp()) + 86400

                    logout_month = (l + relativedelta(months=-1)).timestamp() + 86400
                    
                users.append((i[0],i[1],last,logout_day,logout_week,logout_month))
        
            #print(user)
            text = "Username,Day,Week,Month\n"
            for i in users:

                if(i[2] == 0):
                    hours = 0
                    week = 0
                    month = 0
                    text += "{},{:.1f},{:.1f},{:.1f}\n".format(i[0],hours,week,month)

                else:
                    hours = 0
                    week = 0
                    month = 0
                    log = access_database_with_result(database,"SELECT start,end FROM session,users WHERE session.userid=users.userid and username='{}'".format(i[0]))
                    for j in log:

                        if(j[1] > i[3]):

                            if(j[0] < i[3]):
                                hours += (j[1] - i[3])/3600          
                            else:
                                hours += (j[1] - j[0])/3600

                        if(j[1] > i[4]):

                            if(j[0] < i[4]):
                                week += (j[1] - i[4])/3600          
                            else:
                                week += (j[1] - j[0])/3600

                        if(j[1] > i[5]):

                            if(j[0] < i[5]):
                                month += (j[1] - i[5])/3600          
                            else:
                                month += (j[1] - j[0])/3600

                text += "{},{:.1f},{:.1f},{:.1f}\n".format(i[0],hours,week,month)
                
            encoded = bytes(text, 'utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'text/csv')
            self.send_header("Content-Disposition", 'attachment; filename="{}"'.format('hours.csv'))
            self.send_header("Content-Length", len(encoded))
            self.end_headers()
            self.wfile.write(encoded)

        elif self.path.endswith('/statistics/traffic.csv'):
            ## if we get here, the user is looking for a statistics file
            ## this is where requests for  /statistics/traffic.csv should be handled.
            ## you should check a valid user is checked in. You are encouraged to wrap this behavour in a function.
            
            year = int(datetime.datetime.today().strftime('%Y'))
            month = int(datetime.datetime.today().strftime('%m'))
            day = int(datetime.datetime.today().strftime('%d'))
            current = int(datetime.datetime(year,month,day,0,0).timestamp())

            data = access_database_with_result(database,"SELECT location,type,occupancy FROM traffic WHERE time>={} and mode=1".format(current))
            loc = set()
            typ = set()
            for i in data:
                loc.add(i[0])
                typ.add(i[1])
            loc = list(loc)
            typ = list(typ)
            veh = {}
            veh[0] = 'car'
            veh[1] = 'van'
            veh[2] = 'truck'
            veh[3] = 'taxi'
            veh[4] = 'other'
            veh[5] = 'motorbike'
            veh[6] = 'bicycle'
            veh[7] = 'bus'

            #text = "This should be the content of the csv file."
            text = "Location,Type,Occupancy1,Occupancy2,Occupancy3,Occupancy4\n"

            for i in loc:
                for j in typ:
                    o1 = 0
                    o2 = 0
                    o3 = 0
                    o4 = 0
                    occ = access_database_with_result(database,"SELECT occupancy FROM traffic WHERE time>={} and location='{}' and type={} and mode=1".format(current,i,j))
                    for k in occ:
                        if(k[0] == 1):
                            o1 += 1
                        elif(k[0] == 2):
                            o2 += 1
                        elif(k[0] == 3):
                            o3 += 1
                        elif(k[0] == 4):
                            o4 += 1
                    if(o1 != 0 or o2 != 0 or o3 != 0 or o4 != 0):
                        text += '"{}",{},{},{},{},{}\n'.format(i.lower(),veh[j],o1,o2,o3,o4) # not real data 

            encoded = bytes(text, 'utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'text/csv')
            self.send_header("Content-Disposition", 'attachment; filename="{}"'.format('traffic.csv'))
            self.send_header("Content-Length", len(encoded))
            self.end_headers()
            self.wfile.write(encoded)

        else:
            # A file that does n't fit one of the patterns above was requested.
            self.send_response(404)
            self.end_headers()
        return

def run():
    """This is the entry point function to this code."""
    print('starting server...')
    ## You can add any extra start up code here
    # Server settings
    # Choose port 8081 over port 80, which is normally used for a http server
    if(len(sys.argv)<2): # Check we were given both the script name and a port number
        print("Port argument not provided.")
        return
    server_address = ('127.0.0.1', int(sys.argv[1]))
    httpd = HTTPServer(server_address, myHTTPServer_RequestHandler)
    print('running server on port =',sys.argv[1],'...')
    httpd.serve_forever() # This function will not return till the server is aborted.

run()
