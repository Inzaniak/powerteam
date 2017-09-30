import traceback
import random
import string
import sqlite3
import os
import datetime
import sys
sys.stdout = sys.stderr

import atexit
import cherrypy

vers = 'OFF'

if vers == 'O':
    prefix = '/home/Inzaniak/'
    cherrypy.config.update({'environment': 'embedded'})
else:
    prefix = ''


if cherrypy.__version__.startswith('3.0') and cherrypy.engine.state == 0:
    cherrypy.engine.start(blocking=False)
    atexit.register(cherrypy.engine.stop)

def load_html(in_html,sub_path='html'):
    return open('{}data/{}/{}.html'.format(prefix,sub_path,in_html),'r',encoding='utf-8').read()

def load_home(posts,user,in_html='homenew'):
    conn = sqlite3.connect('{}data/new.db'.format(prefix))
    crs = conn.cursor()
    u = crs.execute('select * from "Users" where Name = "{}"'.format(user.lower())).fetchall()[0][0]
    # Recupero progetti accessibili
    sql_opt = crs.execute("""
    select * from Authorizations A
    left join Projects P
    on P.ID = A.Project
    where User = {}
    """.format(u)).fetchall()
    options = '\n'.join(['<option value="{}">{}</option>'.format(o[2],o[3]) for o in sql_opt])
    #Posts
    post_template = open('{}data/templates/post.html'.format(prefix),'r',encoding='utf-8').read()
    html = open('{}data/html/{}.html'.format(prefix,in_html),'r',encoding='utf-8').read()
    posts_html = ''
    for p in posts:
        out_list = []
        #Gestione URL / Hashtags
        for w in p[5].split():
            if w[0:4].lower() == 'http':
                out_list.append('<a href="{}">{}</a>'.format(w,w))
            elif w[0].lower() == '#':
                out_list.append('<a href="\home?tfilter=%23{}">{}</a>'.format(w[1:],w))
            else:
                out_list.append(w)
        #print(p)
        if p[2] == 0:
            status = """<div class="btn-group pull-right">
                        <a href="/changestatus?postid={p_id}&status=1" class="btn btn-default btn-sm">Complete</a>
                        <a href="/changestatus?postid={p_id}&status=0" class="btn btn-primary btn-sm">WIP</a>
                        <a href="/changestatus?postid={p_id}&status=2" class="btn btn-default btn-sm">TODO</a>
                        </div>
                        <div class="btn-group pull-right">
                            <i class="material-icons">loop</i></p>
                        </div>""".format(p_id=p[0])
        if p[2] == 1:
            status = """<div class="btn-group pull-right">
                        <a href="/changestatus?postid={p_id}&status=1" class="btn btn-primary btn-sm">Complete</a>
                        <a href="/changestatus?postid={p_id}&status=0" class="btn btn-default btn-sm">WIP</a>
                        <a href="/changestatus?postid={p_id}&status=2" class="btn btn-default btn-sm">TODO</a>
                        </div>
                        <div class="btn-group pull-right">
                            <i class="material-icons">check</i></p>
                        </div>""".format(p_id=p[0])
        if p[2] == 2:
            status = """<div class="btn-group pull-right">
                        <a href="/changestatus?postid={p_id}&status=1" class="btn btn-default btn-sm">Complete</a>
                        <a href="/changestatus?postid={p_id}&status=0" class="btn btn-default btn-sm">WIP</a>
                        <a href="/changestatus?postid={p_id}&status=2" class="btn btn-primary btn-sm">TODO</a>
                        </div>
                        <div class="btn-group pull-right">
                            <i class="material-icons">flag</i></p>
                        </div>""".format(p_id=p[0])
        add_info = """
        <div class="panel-body">Update Date: {}</div>
        """.format(p[6])
        # Get reactions
        reactions = crs.execute('select * from reactions where PostID = ?',(p[0],)).fetchall()
        react_up = len([r for r in reactions if r[2]==0])
        react_dng = len([r for r in reactions if r[2]==1])
        react_pr = len([r for r in reactions if r[2]==2])
        reactions_user = crs.execute('select * from reactions where PostID = ? and UserID = ?',(p[0],u)).fetchall()
        user_up = 'btn btn-info'
        user_dng = 'btn btn-info'
        user_pr = 'btn btn-info'
        for r in reactions_user:
            if r[2] == 0:
                user_up = 'btn btn-success'
            if r[2] == 1:
                user_dng = 'btn btn-success'
            if r[2] == 2:
                user_pr = 'btn btn-success'
        posts_html += post_template.format(
                                            user = p[8].title(),
                                            project = p[12],
                                            date = p[4],
                                            activity = ' '.join(out_list),
                                            post_id = p[0],
                                            status = status,
                                            addinfo = add_info
                                            ,user_id = u
                                            ,react1val = react_up
                                            ,react2val = react_dng
                                            ,react3val = react_pr
                                            ,react1 = user_up
                                            ,react2 = user_dng
                                            ,react3 = user_pr
                                           )
        posts_html += '\n<br>\n'
    # Create Post
    create_post = load_html('send_postnew','templates')
    create_post = create_post.format(
                       user_id = u
                       ,date = (datetime.datetime.now()+ datetime.timedelta(hours=2)).strftime('%d/%m/%Y %T')
                       ,options=options
                       )
    conn.close()
    return html.format(posts = posts_html, send_post = create_post,options=options)

class WebSite(object):

    @cherrypy.expose
    def index(self):
        return '<meta http-equiv="refresh" content="0; url=/home">'

    @cherrypy.expose
    def login(self):
        return load_html('login')

    @cherrypy.expose
    def registration(self):
        return load_html('registration')

    @cherrypy.expose
    def projects(self):
        try:
            cherrypy.session['name']
            conn = sqlite3.connect('{}data/new.db'.format(prefix))
            crs = conn.cursor()
            sql_opt = crs.execute('select * from projects').fetchall()
            p_options = '\n'.join(['<option value="{}">{}</option>'.format(o[0],o[1]) for o in sql_opt])
            return load_html('projects').format(options_p=p_options)
        except:
            #print(E)
            print(traceback.format_exc())
            return load_html('login')


    @cherrypy.expose
    def logout(self):
        del cherrypy.session['name']
        return '<meta http-equiv="refresh" content="0; url=/home">'

    @cherrypy.expose
    def authorization(self):
        try:
            cherrypy.session['name']
            conn = sqlite3.connect('{}data/new.db'.format(prefix))
            crs = conn.cursor()
            sql_opt = crs.execute('select * from projects').fetchall()
            p_options = '\n'.join(['<option value="{}">{}</option>'.format(o[0],o[1]) for o in sql_opt])
            sql_opt = crs.execute('select * from users').fetchall()
            u_options = '\n'.join(['<option value="{}">{}</option>'.format(o[0],o[1]) for o in sql_opt])
            return load_html('authorization').format(options_p=p_options,options_u=u_options)
        except:
            #print(E)
            print(traceback.format_exc())
            return load_html('login')

    @cherrypy.expose
    def user(self):
        try:
            cherrypy.session['name']
            conn = sqlite3.connect('{}data/new.db'.format(prefix))
            crs = conn.cursor()
            is_admin = crs.execute('select level from "Users" where name = ?',(cherrypy.session['name'].lower(),)).fetchall()[0][0]
            print(is_admin)
            if is_admin == 0:
                return load_html('user').format(admin='')
            if is_admin == 1:
                users = crs.execute('select name,id from "Users"').fetchall()
                u_options = '\n'.join(['<option value="{}">{}</option>'.format(o[1],o[0]) for o in users])
                posts = crs.execute('select text,id from "Posts"').fetchall()
                p_options = '\n'.join(['<option value="{}">{}</option>'.format(o[1],o[0]) for o in posts])
                admin_out = load_html('user_admin','templates').format(options_u=u_options)
                admin_out += '\n'
                admin_out += load_html('post_admin','templates').format(options_u=p_options)
                return load_html('user').format(admin=admin_out)
        except:
            #print(E)
            print(traceback.format_exc())
            return load_html('login')

    @cherrypy.expose
    def add_auth(self,users,projects):
        try:
            users = users.split()
        except:
            pass
        try:
            projects = projects.split()
        except:
            pass
        conn = sqlite3.connect('{}data/new.db'.format(prefix))
        crs = conn.cursor()
        for p in projects:
            print(p)
            for u in users:
                print(u)
                try:
                    crs.execute('insert into authorizations values(?,?)',(p,u))
                except:
                    pass
        conn.commit()
        return '<meta http-equiv="refresh" content="0; url=/authorization">'

    @cherrypy.expose
    def home(self,tfilter='',status=[0,1,2],project='',date=''):
        try:
            if len(status)>1:
                status = ','.join([str(s) for s in status])
            print(status)
            exc_info = sys.exc_info()
            cherrypy.session['name']
            conn = sqlite3.connect('{}data/new.db'.format(prefix))
            crs = conn.cursor()
            u = crs.execute('select * from "Users" where Name = "{}"'.format(cherrypy.session['name'].lower())).fetchall()[0][0]
            if project != '':
                project = 'and pr.id = "{}"'.format(project)
            posts = crs.execute('''select * from posts p
                                    left join users u
                                    on u.id = p.User
                                    left join Projects pr
                                    on pr.id = p.Project
                                    left join Authorizations a
									on a.Project = p.Project
                                    where (u.Name = "{tf}" or p.Text like "%{tf}%" or pr.Name = "{tf}") 
                                    {pn} 
                                    and p.status in ({st})  
                                    and a.User = "{user}"
                                    and p.Date like "%{date}%"
                                    order by date DESC'''.format(tf=tfilter,st=status,pn=project,user=u,date=date)).fetchall()
            conn.close()
            return load_home(posts,cherrypy.session['name'])
        except Exception as E:
            print(E)
            print(traceback.format_exc())
            return load_html('login')

    @cherrypy.expose
    def changestatus(self,postid,status):
        conn = sqlite3.connect('{}data/new.db'.format(prefix))
        crs = conn.cursor()
        crs.execute('update Posts set Status = ? , DateUpdate = ? where ID = ?',
                (status
                ,(datetime.datetime.now()+ datetime.timedelta(hours=2)).strftime('%d/%m/%Y %T')
                ,postid)
                )
        conn.commit()
        conn.close()
        return "<body onload='location.href = document.referrer; return false;'>"

    @cherrypy.expose
    def add_proj(self,projname):
        conn = sqlite3.connect('{}data/new.db'.format(prefix))
        crs = conn.cursor()
        crs.execute('insert into Projects (Name,CreatedBy,CreatedDate) values (?,?,?)',(projname,cherrypy.session['name'].lower(),(datetime.datetime.now()+ datetime.timedelta(hours=2)).strftime('%d/%m/%Y %T')))
        conn.commit()
        conn.close()
        return "<body onload='location.href = document.referrer; return false;'>"

    @cherrypy.expose
    def add_user(self,name,psw,repsw):
        conn = sqlite3.connect('{}data/new.db'.format(prefix))
        crs = conn.cursor()
        if psw != repsw:
            return "<body onload='location.href = document.referrer; return false;'>"
        try:
            crs.execute('insert into Users (Name,Password) values (?,?)',(name.lower(),psw))
            conn.commit()
        except:
            return "<body onload='location.href = document.referrer; return false;'>"
        conn.close()
        return load_html('login')

    @cherrypy.expose
    def del_proj(self,projname):
        conn = sqlite3.connect('{}data/new.db'.format(prefix))
        crs = conn.cursor()
        crs.execute('delete from projects where ID = ?',(projname,))
        crs.execute('delete from authorizations where Project = ?',(projname,))
        conn.commit()
        conn.close()
        return "<body onload='location.href = document.referrer; return false;'>"

    @cherrypy.expose
    def del_user(self,userid):
        conn = sqlite3.connect('{}data/new.db'.format(prefix))
        crs = conn.cursor()
        if type(userid) == type([]):
            for u in userid:
                crs.execute('delete from users where ID = ?',(u,))
                conn.commit()
        else:  
            crs.execute('delete from users where ID = ?',(userid,))
            conn.commit()
        conn.close()
        return "<body onload='location.href = document.referrer; return false;'>"

    @cherrypy.expose
    def remove_post(self,post_id,multiple=''):
        conn = sqlite3.connect('{}data/new.db'.format(prefix))
        crs = conn.cursor()
        print(post_id)
        if multiple == '':
            crs.execute('delete from posts where ID = ?',(post_id,))
        else:
            crs.execute('delete from posts where ID in ({})'.format(','.join(['"'+str(r)+'"' for r in post_id])))
        conn.commit()
        conn.close()
        return "<body onload='location.href = document.referrer; return false;'>"

    @cherrypy.expose
    def ren_proj(self,projname,newname):
        conn = sqlite3.connect('{}data/new.db'.format(prefix))
        crs = conn.cursor()
        crs.execute('update Projects set Name = ? where ID = ?',(newname,projname))
        conn.commit()
        conn.close()
        return "<body onload='location.href = document.referrer; return false;'>"

    @cherrypy.expose
    def react(self,user_id,post_id,reaction):
        conn = sqlite3.connect('{}data/new.db'.format(prefix))
        crs = conn.cursor()
        try:
            crs.execute('insert into Reactions Values(?,?,?)',(post_id,user_id,reaction))
        except:
            crs.execute('delete from Reactions where PostID = ? and UserID = ? and "Type" = ?',(post_id,user_id,reaction))
        conn.commit()
        conn.close()
        return "<body onload='location.href = document.referrer; return false;'>"

    @cherrypy.expose
    def chg_psw(self,oldpsw,newpsw):
        conn = sqlite3.connect('{}data/new.db'.format(prefix))
        crs = conn.cursor()
        u = crs.execute('select * from "Users" where Name = "{}"'.format(cherrypy.session['name'].lower())).fetchall()[0][0]
        crs.execute('update Users set Password = ? where Password = ? and ID = ?',(newpsw,oldpsw,u))
        conn.commit()
        conn.close()
        return "<body onload='location.href = document.referrer; return false;'>"

    @cherrypy.expose
    def loginnext(self, name,psw):
        conn = sqlite3.connect('{}data/new.db'.format(prefix))
        crs = conn.cursor()
        #print(name.lower(),psw)
        credentials = crs.execute('select * from Users where Name = ? and Password = ?',
                    (name.lower(),psw)).fetchall()
        if len(credentials)==1:
            cherrypy.session['name'] = name
            cherrypy.session['psw'] = psw
            return load_html('loginSuccess')
        else:
            return load_html('loginFail')

    @cherrypy.expose
    def send_post(self,user_id,date,project,text,status):
        conn = sqlite3.connect('{}data/new.db'.format(prefix))
        crs = conn.cursor()
        crs.execute('insert into "Posts" (User,Date,Project,Text,Status) values (?,?,?,?,?)',
                    (user_id,date,project,text,status))
        conn.commit()
        return """<body onload='location.href = document.referrer; return false;'>"""

#print(os.getcwd())
conf = {
    '/': {
        'tools.sessions.on': True,
        'tools.staticdir.root': os.path.abspath(os.getcwd())
    },
    '/static': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': './public'
    }
}
application = cherrypy.Application(WebSite(), script_name='', config=conf)
if __name__ == '__main__':
    cherrypy.quickstart(WebSite(), '/', conf)
