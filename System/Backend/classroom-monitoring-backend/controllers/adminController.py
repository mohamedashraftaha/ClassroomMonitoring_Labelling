# imports all dependencies
from imports.imports import *
from app import *
#######################
"""Admin-level APIs"""    
#######################
class AdminLevelAPIs:
    @adminNamespace.route('/register_admin')
    class register_admin(Resource):    
        registerAdminPostData = api.model ("registerAdminData",{'national_id':fields.String(""),'password':fields.String(""),\
            'first_name':fields.String(""), 'last_name':fields.String(""),'job_role':fields.String("")})
        @api.doc(body=registerAdminPostData)
        def post(self):
            """ @API Description: This API is used to register an admininstrator to the system """
            #getting the request parameters
            try:
                data = request.json
                NationalID = data['national_id']
                password = data['password']
                FirstName = data['first_name']
                LastName = data['last_name']
                position = data['job_role']
            except KeyError:
                    return json.dumps({'status': 'fail', 'message': 'Missing Parameter'})        
            try:
                if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$",password):
                    msg = "Password needs to include Minimum eight characters, at least one letter, one number and one special character"
                    raise NotFound
                salt = password + app.config['SECRET_KEY']
                db_pass = hashlib.md5(salt.encode()).hexdigest()
                newAdmin = db.admin(national_id = NationalID, passwd= db_pass, first_name=FirstName,\
                    last_name=LastName, job_role=position)
                db.classroom_monitoring_db.session.add(newAdmin)
                db.classroom_monitoring_db.session.commit()
            except NotFound:
                return json.dumps({'status': 'fail', 'message': msg})
            except sqlalchemy.exc.IntegrityError as e:
                return json.dumps({'status': 'fail', 'message': "User Already Exists"})

            return json.dumps({'status': 'Success', 'message': "Administrator Added Successfully!"})
    #########################################################################
        @adminNamespace.route('/login_admin')
        class login_admin(Resource): 
 
            loginAdminData = api.model ("loginAdminData",{'national_id':fields.String(""),\
                'password':fields.String("")})
            @api.doc(body = loginAdminData)
            def post(self):            
                """ @API Description: This API is used to login an admininstrator to the system """

                try:
                    data = request.json
                    NationalID = data['national_id']
                    password = data['password']
                    salt = password + app.config['SECRET_KEY']
                    db_pass = hashlib.md5(salt.encode()).hexdigest()
                    user =db.classroom_monitoring_db.session.query(db.admin).filter_by(national_id=NationalID).first()
                    if user is None:
                        raise NotFound
                    if db_pass != user.passwd:
                        raise NotFound
                except KeyError:
                        return json.dumps({'status': 'fail', 'message': 'Missing Parameter'})        
                except NotFound:
                    return json.dumps({'status': 'fail', 'message': "User Not Found"})
                except sqlalchemy.exc.IntegrityError as e:
                    return json.dumps({'status': 'fail', 'message': "User Already Exists"})

                return json.dumps({'status': 'Success', 'message': "Admin logged in successfully!"})
#############################################################################################################
        @adminNamespace.route('/create_exam_instance')
        class create_exam_instance(Resource):
            examInstanceData = api.model ("examInstanceData",{'exam_instance_id':fields.String(""),\
                'exam_reference_code':fields.String(""),\
                    'school_name':fields.String(""), 'admin_national_id':fields.String(""),\
                        'camera_static_ip':fields.String("")})
            @api.doc(body = examInstanceData)
            def post(self):               
                """ @API Description: This API is used to Create Exam Instance """
                try:
                    data = request.json
                    examInstanceID = data['exam_instance_id']
                    examRefCode = data['exam_reference_code']
                    SchoolName = data['school_name']
                    adminNatID = data['admin_national_id']
                    camera_static_ip = data['camera_static_ip']
                
                    # admin not found
                    user =db.classroom_monitoring_db.session.query(db.admin).filter_by(national_id=adminNatID).first()
                    if user is None:
                        raise NotFound
                    
                    # else admin is found
                    newRoom = db.exam_instance(exam_instance_id = examInstanceID, exam_reference_code= examRefCode, school_name=SchoolName,\
                        admin_national_id = adminNatID, camera_static_ip= camera_static_ip)
                    db.classroom_monitoring_db.session.add(newRoom)
                    db.classroom_monitoring_db.session.commit()
                except KeyError:
                        return json.dumps({'status': 'fail', 'message': 'Missing Parameter'})          
                
                except NotFound:
                    return json.dumps({'status': 'fail', 'message': "Admin Not Found"})
                except sqlalchemy.exc.IntegrityError as e:
                    return json.dumps({'status': 'fail', 'message': "exam instance Already Exists"})

                return json.dumps({'status': 'Success', 'message': "exam instance created Successfully!"})
                
    # ##############################################################    
        @adminNamespace.route('/assign_proctor_to_exam')
        class assign_proctor_to_exam(Resource):
            proctorExamAssignmentData = api.model ("proctorExamAssignmentData",{'admin_national_id':fields.String(""),\
                'proctor_national_id':fields.String(""),'exam_instance_id':fields.String("")})
            @api.doc(body = proctorExamAssignmentData)
            def post(self):
                """ @API Description: This API is used to by the admin to assign a proctor to exam instance """
                try:   
                    data = request.json
                    adminNatID = data['admin_national_id']
                    proctorNatID = data['proctor_national_id']
                    examInstanceID = data['exam_instance_id']
                    
                    # admin not found
                    a =db.classroom_monitoring_db.session.query(db.admin).filter_by(national_id=adminNatID).first()
                    if a is None:
                        raise NotFound
                    
                    # admin not found
                    p =db.classroom_monitoring_db.session.query(db.proctor).filter_by(national_id=proctorNatID).first()
                    if p is None:
                        raise NotFound
                    
                    # admin not found
                    eid =db.classroom_monitoring_db.session.query(db.exam_instance).filter_by(exam_instance_id=examInstanceID).first()
                    if eid is None:
                        raise NotFound
                    
                    # else admin is found
                    newAssignment = db.admin_assign_proctor(admin_national_id = adminNatID, proctor_national_id= proctorNatID, \
                        exam_instance_id = examInstanceID)
                    db.classroom_monitoring_db.session.add(newAssignment)
                    db.classroom_monitoring_db.session.commit()
                except KeyError:
                    json.dumps({'status': 'Success', 'message': "exam instance created Successfully!"})

                except NotFound:
                    return json.dumps({'status': 'fail', 'message': "Admin or Proctor or Exam Instance ID Not Found"})
                except sqlalchemy.exc.IntegrityError as e:
                    return json.dumps({'status': 'fail', 'message': "Assignment Already Exists"})

                return json.dumps({'status': 'Success', 'message': "Assignment Completed Successfully!"})
        
    # ###############################################################
        @adminNamespace.route('/register_proctor')
        class register_proctor(Resource):
                registerProctorData = api.model ("registerProctorData",{'national_id':fields.String(""),'password':fields.String(""),\
                    'first_name':fields.String(""), 'last_name':fields.String(""),\
                        'school_name':fields.String("")})
                @api.doc(body=registerProctorData)
                def post(self):
                    """ @API Description: This API is used to register an invigilator to the system """
                    try:  
                        data = request.json
                        NationalID = data['national_id']
                        password = data['password']
                        FirstName = data['first_name']
                        LastName = data['last_name']
                        SchoolName = data['school_name']
                        if not re.match(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$",password):
                            msg = "Password needs to include Minimum eight characters, at least one letter, one number and one special character"
                            raise NotFound
                        salt = password + app.config['SECRET_KEY']
                        db_pass = hashlib.md5(salt.encode()).hexdigest()
                        new_proctor = db.proctor(national_id = NationalID, passwd= db_pass, first_name=FirstName,\
                            last_name=LastName, school_name=SchoolName)
                        db.classroom_monitoring_db.session.add(new_proctor)
                        db.classroom_monitoring_db.session.commit()
                    except KeyError:
                        json.dumps({'status': 'Success', 'message': "exam instance created Successfully!"})
                
                    except sqlalchemy.exc.IntegrityError as e:
                        return json.dumps({'status': 'fail', 'message': "User Already Exists"})

                    return json.dumps({'status': 'Success', 'message': "Proctor Added Successfully!"})

                    ###############################################################