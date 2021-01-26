#!/usr/bin/python3
# npackage example  https://svn.lliurex.net/pandora/n4d-ldap/trunk
# jinja2 http://jinja.pocoo.org/docs/templates

from jinja2 import Environment
from jinja2.loaders import FileSystemLoader
from jinja2 import Template
import tempfile
import shutil
import os
import subprocess
import tarfile
import time
import glob
import n4d.server.core as n4dcore
import n4d.responses
from n4d.utils import get_backup_name, n4d_mv



class ApacheManager:

	def __init__(self):
		#Load template file
		self.core=n4dcore.Core.get_core()
		self.tpl_env = Environment(loader=FileSystemLoader('/usr/share/n4d/templates/apache'))
		self.backup_files=[]
		self.backup_dirs=["/etc/apache2/","/etc/easysites/","/var/www/","/net/server-sync/easy-sites"]
		self.easysites_dirs=["/var/lib/lliurex-www/links/","/usr/share/lliurex-www/srv/icons/"]

	#def init
	
	def startup(self,options):
		# executed when launching n4d
		pass
		
	#def startup

	def apt(self):
		# executed after apt operations
		pass
		
	#def apt
	
	# service test and backup functions #
	def test(self):

		pass

	#def makedir
	def makedir(self,dir=None):

		if not os.path.isdir(dir):
			os.makedirs(dir)
		return [True]

	#def timestamp backup
	def get_time(self):
		return get_backup_name("ApacheManager")

	#def backup
	def backup(self,dir="/backup"):
		
		try:
		
			self.makedir(dir)
			file_path=dir+"/"+self.get_time()
			tar=tarfile.open(file_path,"w:gz")
				
			for f in self.backup_files:
				if os.path.exists(f):
					tar.add(f)

			for d in self.backup_dirs:
				if os.path.exists(d):
					tar.add(d)
			
			'''
			self.list_easy_sites = glob.glob('/var/www/srv/'+'easy-'+'*') + glob.glob("/var/www/srv/links/easy-*")
			
			for j in self.list_easy_sites:
				if os.path.exists(j):
					tar.add(j)

			
			self.list_easy_site_hide=glob.glob("/var/www/srv/links/hide_links/easy-*")
			for j in self.list_easy_site_hide:
				if os.path.exists(j):
					tar.add(j)	
					
			self.list_easy_site_icons=glob.glob("/var/www/srv/icons/easy-*")
			for j in self.list_easy_site_icons:
				if os.path.exists(j):
					tar.add(j)				
			'''
			if os.path.exists(self.easysites_dirs[0]):
				easy_links=glob.glob(self.easysites_dirs[0]+'easy-'+'*')
				for j in easy_links:
					if os.path.exists(j):
						tar.add(j)
			
			if os.path.exists(self.easysites_dirs[1]):
				easy_icons=glob.glob(self.easysites_dirs[1]+'easy-'+'*')
				for j in easy_icons:
					if os.path.exists(j):
						tar.add(j)			
			
			dir="/net/server-sync/easy-sites"
			if os.path.exists(dir):
				cmd="getfacl -pR %s > /tmp/easy-sites.acl"%dir
				os.system(cmd)
				tar.add("/tmp/easy-sites.acl",arcname="easy-sites.acl")
				os.remove("/tmp/easy-sites.acl")
				
				
			os.system("a2query -m > /tmp/mods_available")
			
			tar.add("/tmp/mods_available",arcname="llx-backup_mods_available")
			tar.close()

			#Old n4d: return [True,file_path]
			return n4d.responses.build_successful_call_response(file_path)


		except Exception as e:
			#Old n4d: return [False,str(e)]
			return n4d.responses.build_failed_call_response('',str(e))


	#def restore backup
	def restore(self,file_path=None):


		if file_path==None:
			dir="/backup"
			for f in sorted(os.listdir(dir),reverse=True):
				if "ApacheManager" in f:
					file_path=dir+"/"+f
					break


		try:
			if os.path.exists(file_path):
				tmp_dir=tempfile.mkdtemp()
				tar=tarfile.open(file_path)
				tar.extractall(tmp_dir)
				tar.close()

				os.system("rm -rf %s"%tmp_dir+"/etc/apache2/mods-available")
				os.system("rm -rf %s"%tmp_dir+"/etc/apache2/mods-enabled")
				

				try:
					#Old n4d:if objects["ServerBackupManager"].restoring_version=="14.06":
					if self.core.get_plugin("ServerBackupManager").restoring_version=="14.06":
						
						print("[ApacheManager] Removing old apache conf files...")
						
						files_to_remove=["/etc/apache2/apache2.conf","/etc/apache2/envvars","/etc/apache2/magic","/etc/apache2/ports.conf","/etc/apache2/httpd.conf","/var/www/index.html"]
						
						for f in files_to_remove:
							print(tmp_dir+f,os.path.exists(tmp_dir+f))
							if os.path.exists(tmp_dir+f):
								os.remove(tmp_dir+f)
						os.system("rm -rf %s"%tmp_dir+"/etc/apache2/conf.d")
						os.system("ls -la %s"%tmp_dir+"/etc/apache2/")
						
						
				except Exception as llx1406e:
					print(str(llx1406e))
			


				for f in self.backup_files:
					tmp_path=tmp_dir+f
					if os.path.exists(tmp_path):
						shutil.copy(tmp_path,f)

				for d in self.backup_dirs:
					tmp_path=tmp_dir+d
					if os.path.exists(tmp_path):
						self.makedir(d)
						cmd="cp -r " + tmp_path +"/* "  + d
						os.system(cmd)

				try:
					for d in self.easysites_dirs:
						tmp_path=tmp_dir+d
						tmp_files=glob.glob(tmp_path+'easy-'+'*')
						for file in tmp_files:
							if os.path.exists(file):
								cmd="cp "+file+" "+d
								os.system(cmd)
								if os.path.exists(os.path.join(d,os.path.basename(file))):
									if 'lib/lliurex-www/links' in os.path.join(d,os.path.basename(file)):
										cmd="chown www-data:www-data "+ os.path.join(d,os.path.basename(file))
										os.system(cmd)
				
				except:
					pass						
				#Add pmb redirection to port 800 (apache2-lliurex)
				sw_loadProxyMods=False
				for confFile in ["/etc/apache2/sites-enabled/pmb.conf","/etc/apache2/sites-enabled/opac.conf"]:
					if os.path.exists(confFile):
						sw_loadProxyMods=True
						site=confFile.split('/')[-1]
						site=site.replace('.conf','')
						confF=open(confFile,'r')
						contentF=confF.readlines()
						confF.close()
						pos=0
						aliasPos=0
						for line in contentF:
							pos=pos+1
							if "Alias " in line:
								aliasPos=pos
							if "ProxyPass" in line:
								aliasPos=-1
								break

						if aliasPos>0:
							contentF.insert(aliasPos,"\n\tProxyPass / http://"+site+":800/\n\tProxyPassReverse / http://"+site+":800/\n")
							confF=open(confFile,'w')
							confF.writelines(contentF)
							confF.close()

				if sw_loadProxyMods:	
					#Ensure that proxy mods are enabled
					cmd="/usr/sbin/a2enmod proxy proxy_http"
					os.system(cmd)

				if os.path.exists("/net/server-sync/easy-sites") and os.path.exists(tmp_dir+"/easy-sites.acl"):
					os.system("setfacl -R --restore=%s/easy-sites.acl"%tmp_dir)
					
				
				
				# # 14.06 -> 15.05 CASE #############################
				
				try:
					#Old n4d: if objects["ServerBackupManager"].restoring_version=="14.06":
					if self.core.get_plugin("ServerBackupManager").restoring_version=="14.06":

						
						print("[ApacheManager] Fixing files ...")
						
						dir="/etc/apache2/sites-available/"
						
						for item in os.walk(dir):
							path,data,files=item
						
						for f in files:
							path=dir+f
							if not os.path.exists(path):
								continue
							if f=="default":
								os.remove(path)
								continue
								if os.path.exists(dir+"000-default.conf"):
									os.remove(dir+"000-default.conf")
								os.symlink("/etc/apache2/sites-available/llx-default.conf",dir+"000-default.conf")
							elif f=="default.lliurex":
								os.remove(path)
								continue
							elif f=="000-default.orig":
								pass
							elif not f.endswith(".conf"):
								shutil.move(path,path+".conf")

						print(dir,"DONE")

						dir="/etc/apache2/sites-enabled/"
						files=[]
						
						for item in os.walk(dir):
							path,data,files=item

						
						for f in files:
							path=dir+f
							link=os.readlink(path)
							if link.startswith("../"):
								link=link.replace("../","/etc/apache2/")
							
							if f=="000-default":
								os.remove(path)
								if os.path.exists("/etc/apache2/sites-enabled/000-default.conf"):
									os.remove("/etc/apache2/sites-enabled/000-default.conf")
								os.symlink("/etc/apache2/sites-available/000-default.conf","/etc/apache2/sites-enabled/000-default.conf")
								continue
							

							
							if not path.endswith(".conf"):
								os.remove(path)
								if not os.path.exists(link):
									link+=".conf"
								
								if not os.path.exists(link):
									continue
								if os.path.exists(path+".conf"):
									os.remove(path+".conf")
								os.symlink(link,path+".conf")
								
							else:
								if not os.path.exists(link):
									os.remove(path)
								
						
				except Exception as llx14_ex:
					print(str(llx14_ex))
					
				# #END OF 14.06->15.05 CASE # ############
				
				os.system("service apache2 restart")
				
				#Old n4d: return [True,""]
				return n4d.responses.build_successful_call_response(True)


			else:
				#Old n4d:return [False,"Backup file not found"]
				return n4d.responses.build_successful_call_response(False,"Backup file not found")


		except Exception as e:

			#Old n4d: return [False,str(e)]
			return n4d.responses.build_failed_call_response('',str(e))



	#def restore

	def load_exports(self):
		#Get template
		template_server = self.tpl_env.get_template("server")
		list_variables = {}
		
		#Inicialize INTERNAL_DOMAIN
		#Old n4d: list_variables['INTERNAL_DOMAIN'] = objects['VariablesManager'].get_variable('INTERNAL_DOMAIN')
		list_variables['INTERNAL_DOMAIN']=self.core.get_variable('INTERNAL_DOMAIN')["return"]
		
		#If INT_DOMAIN is not defined calculate it with args values
		if  list_variables['INTERNAL_DOMAIN'] == None:
			#Old n4d: return {'status':False,'msg':'Variable INTERNAL_DOMAIN not defined'}
			return n4d.responses.build_failed_call_response('','Variable INTERNAL_DOMAIN not defined')
		
		#Inicialize INTERNAL_DOMAIN
		#Old n4d: list_variables['HOSTNAME'] = objects['VariablesManager'].get_variable('HOSTNAME')
		list_variables['HOSTNAME']=self.core.get_variable('HOSTNAME')['return']
		
		#If INT_DOMAIN is not defined calculate it with args values
		if  list_variables['HOSTNAME'] == None:
			#Old n4d: return {'status':False,'msg':'Variable HOSTNAME not defined'}
			return n4d.responses.build_failed_call_response('','Variable HOSTNAME not defined')
		
		###########################
		#Setting VARS
		###########################
		
		#Set HTTP_PATH 
		#Old n4d: list_variables['HTTP_PATH'] = objects['VariablesManager'].get_variable('HTTP_PATH')
		list_variables['HTTP_PATH']=self.core.get_variable('HTTP_PATH')["return"]

		#If variable PROXY_ENABLED is not defined calculate it with args values
		if  list_variables['HTTP_PATH'] == None:
			#Old n4d: status,list_variables['HTTP_PATH'] = objects['VariablesManager'].init_variable('HTTP_PATH',{'PATH':'/var/www/'})
			ret=self.core.set_variable('HTTP_PATH','/var/www/')
			list_variables['HTTP_PATH']=ret['return']
			if ret['status']==0:
				status=True
			else:
				status=False

		#Encode vars to UTF-8
		#Old n4d: string_template = template_server.render(list_variables).encode('UTF-8')
		string_template = template_server.render(list_variables)
		
		#Open template file
		fd, tmpfilepath = tempfile.mkstemp()
		new_export_file = open(tmpfilepath,'w')
		new_export_file.write(string_template)
		new_export_file.close()
		os.close(fd)
		#Write template values
		n4d_mv(tmpfilepath,'/etc/apache2/sites-available/server.conf',True,'root','root','0644',False )
		#Restart service
		subprocess.Popen(['a2ensite','server.conf'],stdout=subprocess.PIPE).communicate()
		subprocess.Popen(['/etc/init.d/apache2','reload'],stdout=subprocess.PIPE).communicate()
		#Old n4d: return {'status':True,'msg':'Exports written'}
		return n4d.responses.build_successful_call_response('','Exports written')

	#def load_exports

	def reboot_apache(self):
		#Restart apache service
		subprocess.Popen(['/etc/init.d/apache2','restart'],stdout=subprocess.PIPE).communicate()
		#Old n4d: return {'status':True,'msg':'apache2 rebooted'}
		return n4d.responses.build_successful_call_response('','apache2 rebooted')

	#def reboot_squid
	

	# ######################### #
	
#class ApacheManager
