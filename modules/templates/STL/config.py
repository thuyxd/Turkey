# -*- coding: utf-8 -*-

try:
    # Python 2.7
    from collections import OrderedDict
except:
    # Python 2.6
    from gluon.contrib.simplejson.ordered_dict import OrderedDict

from gluon import current
from gluon.storage import Storage

def config(settings):
    """
        Settings for the SupportToLife deployment in Turkey
    """

    T = current.T

    settings.base.system_name = T("Sahana Refugee Case Management")
    #settings.base.system_name_short = T("Sahana")

    # PrePopulate data
    settings.base.prepopulate += ("STL", "default/users", "STL/Demo")

    # Theme (folder to use for views/layout.html)
    #settings.base.theme = "STL"

    # Authentication settings
    # Should users be allowed to register themselves?
    settings.security.self_registration = False
    # Do new users need to verify their email address?
    #settings.auth.registration_requires_verification = True
    # Do new users need to be approved by an administrator prior to being able to login?
    #settings.auth.registration_requires_approval = True
    settings.auth.registration_requests_organisation = True

    # Approval emails get sent to all admins
    #settings.mail.approver = "ADMIN"

    # Restrict the Location Selector to just certain countries
    # NB This can also be over-ridden for specific contexts later
    # e.g. Activities filtered to those of parent Project
    #settings.gis.countries = ("TR",)
    # Uncomment to display the Map Legend as a floating DIV
    settings.gis.legend = "float"
    # Uncomment to Disable the Postcode selector in the LocationSelector
    #settings.gis.postcode_selector = False # @ToDo: Vary by country (include in the gis_config!)
    # Uncomment to show the Print control:
    # http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/MapPrinting
    #settings.gis.print_button = True

    # L10n settings
    # Languages used in the deployment (used for Language Toolbar & GIS Locations)
    # http://www.loc.gov/standards/iso639-2/php/code_list.php
    settings.L10n.languages = OrderedDict([
        ("ar", "العربية"),
        ("en", "English"),
        ("tr", "Türkçe"),
    ])
    # Default language for Language Toolbar (& GIS Locations in future)
    settings.L10n.default_language = "tr"
    # Uncomment to Hide the language toolbar
    #settings.L10n.display_toolbar = False
    # Default timezone for users
    settings.L10n.utc_offset = "+0200"
    # Number formats (defaults to ISO 31-0)
    # Decimal separator for numbers (defaults to ,)
    settings.L10n.decimal_separator = ","
    # Thousands separator for numbers (defaults to space)
    settings.L10n.thousands_separator = "."
    # Uncomment this to Translate Layer Names
    settings.L10n.translate_gis_layer = True
    # Uncomment this to Translate Location Names
    settings.L10n.translate_gis_location = True
    # Uncomment this to Translate Organisation Names/Acronyms
    settings.L10n.translate_org_organisation = True
    # Finance settings
    settings.fin.currencies = {
        "EUR" : "Euros",
        #"GBP" : "Great British Pounds",
        "TRY" : "Turkish Lira",
        "USD" : "United States Dollars",
    }
    settings.fin.currency_default = "TRY"

    # Security Policy
    # http://eden.sahanafoundation.org/wiki/S3AAA#System-widePolicy
    # 1: Simple (default): Global as Reader, Authenticated as Editor
    # 2: Editor role required for Update/Delete, unless record owned by session
    # 3: Apply Controller ACLs
    # 4: Apply both Controller & Function ACLs
    # 5: Apply Controller, Function & Table ACLs
    # 6: Apply Controller, Function, Table ACLs and Entity Realm
    # 7: Apply Controller, Function, Table ACLs and Entity Realm + Hierarchy
    # 8: Apply Controller, Function, Table ACLs, Entity Realm + Hierarchy and Delegations
    #
    settings.security.policy = 8 # Entity Realm + Hierarchy and Delegations

    # Uncomment to have Person records owned by the Org they are an HR for
    settings.auth.person_realm_human_resource_site_then_org = True

    # -------------------------------------------------------------------------
    # Uncomment to allow hierarchical categories of Skills, which each need their own set of competency levels.
    #settings.hrm.skill_types = True

    # Uncomment to have Volunteers be hierarchical organisational units
    # (& hence HR realms propagate down to Address & Contacts)
    # NB Doesn't seem to make any difference
    #settings.hrm.vol_affiliation = 1

    # -------------------------------------------------------------------------
    # Uncomment to Commit Named People rather than simply Anonymous Skills
    settings.req.commit_people = True

    # Disable Inline Forms, unless we enable separate controllers
    # (otherwise Create form cannot redirect to next tab correctly)
    settings.req.inline_forms = False

    # -------------------------------------------------------------------------
    # Person Registry
    #
    # Allow third gender
    settings.pr.hide_third_gender = False

    # -------------------------------------------------------------------------
    def pr_component_realm_entity(table, row):
        """
            Assign a Realm Entity to Person Address/Contact records
        """

        db = current.db
        s3db = current.s3db

        # Find the Person
        ptable = s3db.pr_person
        person = db(ptable.pe_id == row.pe_id).select(ptable.id,
                                                      limitby=(0, 1)
                                                      ).first()
        try:
            person_id = person.id
        except:
            # => Set to default of Person's
            return row.pe_id

        # Find the Organisation which this Person links to
        htable = s3db.hrm_human_resource
        query = (htable.person_id == person_id) & \
                (htable.deleted == False)
        hrs = db(query).select(htable.organisation_id)
        if len(hrs) != 1:
            # Either no HR record or multiple options
            # => Set to default of Person's
            return row.pe_id
        organisation_id = hrs.first().organisation_id

        # Find the Org's realm_entity
        otable = s3db.org_organisation
        org = db(otable.id == organisation_id).select(otable.realm_entity,
                                                      limitby=(0, 1)
                                                      ).first()
        try:
            # Set to the same realm_entity
            return org.realm_entity
        except:
            # => Set to default of Person's
            return row.pe_id

    # -------------------------------------------------------------------------
    def customise_pr_address_resource(r, tablename):

        current.s3db.configure("pr_address",
                               realm_entity = pr_component_realm_entity,
                               )

    settings.customise_pr_address_resource = customise_pr_address_resource

    # -------------------------------------------------------------------------
    def customise_pr_contact_resource(r, tablename):

        current.s3db.configure("pr_contact",
                               realm_entity = pr_component_realm_entity,
                               )

    settings.customise_pr_contact_resource = customise_pr_contact_resource

   

    # -------------------------------------------------------------------------
    def vol_rheader(r):
        if r.representation != "html":
            # RHeaders only used in interactive views
            return None
        record = r.record
        if record is None:
            # List or Create form: rheader makes no sense here
            return None

        #from gluon.html import DIV
        person_id = r.id
        s3db = current.s3db
        table = s3db.hrm_human_resource
        hr = current.db(table.person_id == person_id).select(table.organisation_id,
                                                             limitby=(0, 1)).first()
        if hr:
            if current.auth.user.organisation_id != hr.organisation_id:
                # Only show Org if not the same as user's
                rheader = table.organisation_id.represent(hr.organisation_id)
            else:
                rheader = None
        else:
            # Something went wrong!
            rheader = None
        return rheader

    # -------------------------------------------------------------------------
    def customise_pr_person_controller(**attr):

        s3db = current.s3db
        s3 = current.response.s3

        # Custom prep
        standard_prep = s3.prep
        def custom_prep(r):
            
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True
            
            auth = current.auth
            has_role = auth.s3_has_role
            
            if r.controller == "dvr" and not r.component:
                from s3 import IS_NOT_EMPTY
                from gluon import IS_EMPTY_OR

                ctable = s3db.dvr_case
                cttable = s3db.dvr_case_type_case
                
                #General Default Values
                s3db.pr_person_details.nationality.default = "SY"
                s3db.pr_identity.type.default = 50
                
                
                # Require organisation, site and status
                for fn in ("organisation_id",
                           "site_id",                           
                           ):
                    field = ctable[fn]
                    requires = field.requires
                    if isinstance(requires, IS_EMPTY_OR):
                        field.requires = requires.other

                root_org = current.auth.root_org()

                if root_org:
                    # Set default for organisation_id and hide the field
                    field = ctable.organisation_id
                    field.default = root_org
                    field.readable = field.writable = False

                    # Hide organisation_id in list_fields, too
                    list_fields = r.resource.get_config("list_fields")
                    if "dvr_case.organisation_id" in list_fields:
                        list_fields.remove("dvr_case.organisation_id")

                    # Limit sites to root_org
                    field = ctable.site_id
                    requires = field.requires
                    if requires:
                        if isinstance(requires, IS_EMPTY_OR):
                            requires = requires.other
                        if hasattr(requires, "dbset"):
                            stable = s3db.org_site
                            query = (stable.organisation_id == root_org)
                            requires.dbset = current.db(query)


                resource = r.resource
                if r.interactive:

                    # Custom CRUD form
                    from s3 import S3SQLCustomForm, S3SQLInlineComponent, S3SQLInlineLink
                    deletable = False
                    if has_role("ADMIN"):   
                        deletable = True                     
                        crud_form = S3SQLCustomForm(
                                    S3SQLInlineLink("case_type",
                                                        field = "case_type_id",
                                                        label = T("Record Type"),
                                                        cols = 3,
                                                        required=True,                                                        
                                                        ),
                                    "dvr_case.pss_reference",
                                    "dvr_case.reference",
                                    "dvr_case.date",
                                    "dvr_case.organisation_id",
                                    "dvr_case.site_id",
                                    "first_name",                                    
                                    "last_name",
                                    "date_of_birth",
                                    "gender",
                                    "person_details.marital_status",
                                    #S3SQLInlineComponent(
                                    #        "contact",
                                    #        fields = [("", "value"),
                                    #                  ],
                                    #        filterby = {"field": "contact_method",
                                    #                    "options": "EMAIL",
                                    #                    },
                                    #        label = T("Email"),
                                    #        multiple = False,
                                    #        name = "email",
                                    #        ),
                                    S3SQLInlineComponent(
                                            "contact",
                                            fields = [("", "value"),
                                                      ],
                                            filterby = {"field": "contact_method",
                                                        "options": "SMS",
                                                        },
                                            label = T("Mobile Phone"),
                                            multiple = False,
                                            name = "phone",
                                            ),
                                    "person_details.nationality",
                                    "person_details.literacy",
                                    S3SQLInlineComponent(
                                            "case_language",
                                            fields = ["language",
                                                      "quality",
                                                      "comments",
                                                      ],
                                            label = T("Language / Communication Mode"),
                                            ),
                                    S3SQLInlineComponent(
                                            "contact_emergency",
                                            fields = ["name",
                                                      "relationship",
                                                      "phone",
                                                      ],
                                            label = T("Emergency Contact"),
                                            multiple = False,
                                            ),
                                    S3SQLInlineComponent(
                                            "identity",
                                            fields = ["type",
                                                      "description",
                                                      "value",
                                                      ],
                                            ),
                                    S3SQLInlineComponent(
                                            "address",
                                            label = T("Current Address"),
                                            fields = [("", "location_id"),
                                                      ],
                                            filterby = {"field": "type",
                                                        "options": "1",
                                                        },
                                            link = False,
                                            multiple = False,
                                            ),
                                    "dvr_case.head_of_household",
                                    "dvr_case.hoh_name",
                                    "dvr_case.hoh_gender",
                                    "dvr_case.hoh_relationship",
                                    "dvr_case.comments",
                                    )
                    elif has_role("ORG_ADMIN"):
                        # Require fields
                        ctable.reference.requires = IS_NOT_EMPTY()
                        
                        #Default Values
                        cttable.case_type_id.default = 2
                                               
                        crud_form = S3SQLCustomForm(
                                    S3SQLInlineLink("case_type",
                                                        field = "case_type_id",
                                                        label = T("Record Type"),
                                                        cols = 3, 
                                                        required=True,                                                       
                                                        ),                                    
                                    "dvr_case.reference",                                    
                                    "dvr_case.date",
                                    "dvr_case.organisation_id",
                                    "dvr_case.site_id",
                                    "first_name",
                                    "last_name",
                                    "date_of_birth",
                                    "gender",
                                    "person_details.marital_status",                                    
                                    S3SQLInlineComponent(
                                            "contact",
                                            fields = [("", "value"),
                                                      ],
                                            filterby = {"field": "contact_method",
                                                        "options": "SMS",
                                                        },
                                            label = T("Mobile Phone"),
                                            multiple = False,
                                            name = "phone",
                                            ),
                                    "person_details.nationality",
                                    "person_details.literacy",
                                    S3SQLInlineComponent(
                                            "case_language",
                                            fields = ["language",
                                                      "quality",
                                                      "comments",
                                                      ],
                                            label = T("Language / Communication Mode"),
                                            ),
                                    S3SQLInlineComponent(
                                            "contact_emergency",
                                            fields = ["name",
                                                      "relationship",
                                                      "phone",
                                                      ],
                                            label = T("Emergency Contact"),
                                            multiple = False,
                                            ),
                                    S3SQLInlineComponent(
                                            "identity",
                                            fields = ["type",
                                                      "description",
                                                      "value",
                                                      ],
                                            ),
                                    S3SQLInlineComponent(
                                            "address",
                                            label = T("Current Address"),
                                            fields = [("", "location_id"),
                                                      ],
                                            filterby = {"field": "type",
                                                        "options": "1",
                                                        },
                                            link = False,
                                            multiple = False,
                                            ),
                                    "dvr_case.head_of_household",
                                    "dvr_case.hoh_name",
                                    "dvr_case.hoh_gender",
                                    "dvr_case.hoh_relationship",
                                    "dvr_case.comments",
                                    )
                    elif has_role("PSS_ADMIN"):   
                        # Require fields
                        ctable.pss_reference.requires = IS_NOT_EMPTY()
                        
                        #Default Values
                        cttable.case_type_id.default = 1
                        
                        crud_form = S3SQLCustomForm(
                                    S3SQLInlineLink("case_type",
                                                        field = "case_type_id",
                                                        label = T("Record Type"),
                                                        cols = 3,   
                                                        required=True,                                                     
                                                        ),                                    
                                    "dvr_case.pss_reference", 
                                    "dvr_case.date",                                   
                                    "dvr_case.organisation_id",
                                    "dvr_case.site_id",
                                    "first_name",
                                    "last_name",
                                    "date_of_birth",
                                    "gender",
                                    "person_details.marital_status",                                    
                                    S3SQLInlineComponent(
                                            "contact",
                                            fields = [("", "value"),
                                                      ],
                                            filterby = {"field": "contact_method",
                                                        "options": "SMS",
                                                        },
                                            label = T("Mobile Phone"),
                                            multiple = False,
                                            name = "phone",
                                            ),
                                    "person_details.nationality",
                                    "person_details.literacy",
                                    S3SQLInlineComponent(
                                            "case_language",
                                            fields = ["language",
                                                      "quality",
                                                      "comments",
                                                      ],
                                            label = T("Language / Communication Mode"),
                                            ),
                                    S3SQLInlineComponent(
                                            "contact_emergency",
                                            fields = ["name",
                                                      "relationship",
                                                      "phone",
                                                      ],
                                            label = T("Emergency Contact"),
                                            multiple = False,
                                            ),
                                    S3SQLInlineComponent(
                                            "identity",
                                            fields = ["type",
                                                      "description",
                                                      "value",
                                                      ],
                                            ),
                                    S3SQLInlineComponent(
                                            "address",
                                            label = T("Current Address"),
                                            fields = [("", "location_id"),
                                                      ],
                                            filterby = {"field": "type",
                                                        "options": "1",
                                                        },
                                            link = False,
                                            multiple = False,
                                            ),
                                    "dvr_case.comments",
                                    )

                    # Extend filter widgets
                    from s3 import s3_get_filter_opts, S3TextFilter, S3OptionsFilter
                    filter_widgets = [
                        S3TextFilter(["first_name",                                      
                                      "last_name",
                                      "email.value",
                                      "phone.value",
                                      "dvr_case.reference",
                                      "dvr_case.pss_reference",
                                      "pr_identity.value"
                                      ],
                                      label = T("Search"),                                      
                                      ),
                        S3OptionsFilter("dvr_case_type_case.case_type_id",
                                        options = lambda: s3_get_filter_opts("dvr_case_type"),                                        
                                        ),
                        S3OptionsFilter("age_group",
                                        hidden = True,                                        
                                        ),
                        S3OptionsFilter("case_language.language",
                                        hidden = True,                                        
                                        ),
                        S3OptionsFilter("person_details.literacy",
                                        hidden = True,                                        
                                        ),
                    ]
                        
                    if has_role("ORG_ADMIN"):
                        filter_widgets.append(
                            S3OptionsFilter("dvr_case_activity.need_id",
                                            options = lambda: s3_get_filter_opts("dvr_need"),
                                            hidden = True,
                                            )
                            )                        

                    resource.configure(crud_form = crud_form,
                                       filter_widgets = filter_widgets,
                                       deletable = deletable
                                       )
                    # Hide Postcode in addresses (not used)
                    atable = s3db.pr_address
                    from s3 import S3LocationSelector
                    location_id = atable.location_id
                    location_id.widget = S3LocationSelector(show_address=True,
                                                            show_postcode = False,
                                                            )

                    # Inject filter script for sites (filter by selected org)
                    if not root_org:
                        script = '''$.filterOptionsS3({
'trigger':'sub_dvr_case_organisation_id',
'target':'sub_dvr_case_site_id',
'lookupResource':'site',
'lookupPrefix':'org',
'lookupField':'site_id',
'lookupKey':'organisation_id'
})'''
                        s3.jquery_ready.append(script)

                    # Expose additional case fields:
                    fields = ("head_of_household",
                              "hoh_name",
                              "hoh_gender",
                              "hoh_relationship"
                              )
                    for fname in fields:
                        field = ctable[fname]
                        field.readable = field.writable = True

                    # Inject script to toggle Head of Household form fields
                    path = "/%s/static/themes/STL/js/dvr.js" % current.request.application
                    if path not in s3.scripts:
                        s3.scripts.append(path)

                # Custom list fields (must be outside of r.interactive)
                list_fields = ["first_name",                       
                       "last_name",
                       "date_of_birth",
                       "gender",
                       (T("Phone"), "phone.value"),
                       (T("Email"),"email.value")
                    ]
                if has_role("ADMIN"):
                    list_fields.insert(0,
                        "dvr_case_type_case.case_type_id"
                        )
                    list_fields.insert(1,
                        "dvr_case.reference"
                        )
                    list_fields.insert(2,
                        "dvr_case.pss_reference"
                        )
                elif has_role("ORG_ADMIN"):
                    list_fields.insert(0,
                        "dvr_case.reference"
                        )
                elif has_role("PSS_ADMIN"):
                    list_fields.insert(0,
                        "dvr_case.pss_reference"
                        )
                    
                resource.configure(list_fields = list_fields,
                                   #orderby = "dvr_case.priority desc",
                                   )
                
            elif r.controller == "dvr" and r.component_name == "case_activity":
                
                s3db.dvr_case_activity.completed.writable = s3db.dvr_case_activity.completed.readable = False
                
                #Customize Case Activity Tab
                s3db.configure("dvr_case_activity",
                               list_fields = ["case_activity_type_id",
                                              "priority",
                                              "status",                                              
                                              "start_date",
                                              "need_id",                                              
                                              "followup",
                                              "followup_date"
                                              ],
                               )
            elif r.controller == "dvr" and r.component_name == "training":                                
                #Customize Training Tab
                s3db.configure("hrm_training",  
                               list_fields = ["course_id",
                                              "training_event_id$name",
                                              "training_event_id$start_date",
                                              "training_event_id$end_date"
                                ],
                               )
            return result
        s3.prep = custom_prep
        attr["rheader"] = dvr_rheader
        return attr

    settings.customise_pr_person_controller = customise_pr_person_controller
    
    # -------------------------------------------------------------------------
    def customise_dvr_case_activity_controller(**attr):
        # Custom RHeader
        s3 = current.response.s3
        standard_prep = s3.prep  
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True
            if r.controller == "dvr":
                s3db = current.s3db
                
                from s3 import s3_get_filter_opts, S3TextFilter, S3OptionsFilter, S3DateFilter
                gender_opts = dict(s3db.pr_gender_opts)
                filter_widgets = [
                    S3TextFilter(["person_id$first_name",                                  
                                  "person_id$last_name",                                  
                                  "case_id$reference",
                                  ],
                                  label = T("Search"),
                                  comment = T("You can search by name, case number"),
                                  ),
                    S3OptionsFilter("case_activity_type_id",
                                    options = lambda: s3_get_filter_opts("dvr_case_activity_type"),
                                    hidden = True,
                                    ),
                    S3OptionsFilter("person_id$gender",   
                                    options = gender_opts,                                 
                                    hidden = True,
                                    ),                    
                    S3OptionsFilter("followup",                                      
                                      options = {True: T("Yes"),
                                                 False: T("No"),
                                                 },
                                      cols = 2,
                                      hidden = True,
                                      ),
                    S3DateFilter("followup_date",
                                       cols = 2,
                                       hidden = True,
                                       ),
                    S3DateFilter("person_id$date_of_birth",
                                       cols = 2,
                                       hidden = True,
                                       ),
                    S3DateFilter("start_date",
                                       cols = 2,
                                       hidden = True,
                                       ),
                ]
                list_fields = ["case_id$reference",
                               "person_id",
                               "case_activity_type_id",
                               "need_id",
                               "need_details",
                               "status",
                               "priority",
                               "followup",
                               "followup_date",
                               ]
                s3db.configure("dvr_case_activity",
                               list_fields = list_fields,
                               filter_widgets = filter_widgets,
                               )  
                                                                
            return result
        
        s3.prep = custom_prep
        return attr

    settings.customise_dvr_case_activity_controller = customise_dvr_case_activity_controller
    
    # =============================================================================
    def customise_hrm_training_event_controller(**attr):
        """ Configure hrm_training_contyroller """  
        s3 = current.response.s3
        standard_prep = s3.prep  
        
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True
            
            if r.controller == "dvr":
                from s3 import IS_NOT_EMPTY
                s3db = current.s3db
                s3db.hrm_training_event.name.readable = s3db.hrm_training_event.name.writable = True
                s3db.hrm_training_event.name.requires = IS_NOT_EMPTY() 
                
                s3db.configure("hrm_training",
                        list_fields = ["person_id$person_id:dvr_case.pss_reference",                                       
                                       "person_id",
                                       "person_id$gender",
                                       "person_id$age",
                                       ],
                       )
                s3db.configure("hrm_training_event",
                        list_fields = ["course_id$code",
                                       "course_id",
                                       "name",
                                       "start_date",
                                       "end_date",
                                       "hours",
                                       "instructor",                                                                
                                       ],
                       )
                                                                
            return result
        
        s3.prep = custom_prep  
        return attr
    
    settings.customise_hrm_training_event_controller = customise_hrm_training_event_controller
    
    # =============================================================================
    def customise_hrm_training_controller(**attr):
        """ Configure hrm_training_contyroller """  
        s3 = current.response.s3
        standard_prep = s3.prep  
        
        def custom_prep(r):
            # Call standard prep
            if callable(standard_prep):
                result = standard_prep(r)
            else:
                result = True
            
            if r.controller == "dvr":
                s3db = current.s3db
                
                from s3 import s3_get_filter_opts, S3TextFilter, S3OptionsFilter, S3DateFilter
                filter_widgets = [
                    S3TextFilter(["person_id$first_name",                                  
                                  "person_id$last_name", 
                                  "training_event_id$name"                                 
                                  ],
                                  label = T("Search"),                                  
                                  ),
                    S3OptionsFilter("course_id",
                                    options = lambda: s3_get_filter_opts("hrm_course"),
                                    hidden = True,                                    
                                    ),
                    S3OptionsFilter("training_event_id$site_id",                                    
                                    hidden = True,                                    
                                    ),
                    S3DateFilter("training_event_id$start_date",
                                       cols = 2,
                                       hidden = True,
                                       ),
                ]
                
                s3db.configure("hrm_training",
                        list_fields = ["person_id$person_id:dvr_case.pss_reference",                                       
                                       "person_id",
                                       "person_id$gender",
                                       "person_id$age",
                                       "course_id",
                                       "training_event_id$name",
                                       "training_event_id$start_date",
                                       "training_event_id$end_date"                                    
                                       ],
                        filter_widgets = filter_widgets,
                       )
                                                                
            return result
        
        s3.prep = custom_prep  
        return attr
    
    settings.customise_hrm_training_controller = customise_hrm_training_controller
    
    # =============================================================================
    def dvr_rheader(r, tabs=[]):
        """ DVR module resource headers """
    
        if r.representation != "html":
            # Resource headers only used in interactive views
            return None

        auth = current.auth
        has_role = auth.s3_has_role
            
        from s3 import s3_rheader_resource, S3ResourceHeader, s3_fullname
        tablename, record = s3_rheader_resource(r)
        if tablename != r.tablename:
            resource = current.s3db.resource(tablename, id=record.id)
        else:
            resource = r.resource
    
        rheader = None
        rheader_fields = []
    
        if record:
            T = current.T
    
            if tablename == "pr_person":
    
                if not tabs:
                    if has_role("ORG_ADMIN"):                        
                        tabs = [(T("Basic Details"), None),
                                (T("Activities"), "case_activity"),
                                (T("Beneficiaries"), "beneficiary_data"),
                                (T("Economy"), "economy"),
                                (T("Service Contacts"), "case_service_contact"),
                                (T("Training"), "training"),                        
                                ]
                    elif has_role("PSS_ADMIN"):
                        tabs = [(T("Basic Details"), None),                                
                                (T("Training"), "training"),                        
                                ]
    
                case = resource.select(["dvr_case.reference",
                                        "dvr_case.pss_reference",                                        
                                        ],
                                        represent=True,
                                        ).rows
                if case:
                    case = case[0]
                    case_reference = lambda row: case["dvr_case.reference"]
                    case_pss_reference = lambda row: case["dvr_case.pss_reference"]
                    
                else:
                    # Target record exists, but doesn't match filters
                    return None
                rheader_fields = [[("first_name"),("last_name")],
                                  [("date_of_birth")],
                                  ]
                if has_role("ORG_ADMIN"):
                    rheader_fields.insert(0,[(T("Case Number"), case_reference)])
                elif has_role("PSS_ADMIN"):
                    rheader_fields.insert(0,[(T("PSS ID"), case_pss_reference)])
    
            elif tablename == "dvr_case":
    
                if not tabs:
                    tabs = [(T("Basic Details"), None),
                            (T("Activities"), "case_activity"),
                            ]
    
                rheader_fields = [["reference"],
                                  ["status_id"],
                                  ]
    
            rheader = S3ResourceHeader(rheader_fields, tabs)(r,
                                                             table=resource.table,
                                                             record=record,
                                                             )
    
        return rheader
    
    # -------------------------------------------------------------------------
    # Comment/uncomment modules here to disable/enable them
    # Modules menu is defined in modules/eden/menu.py
    settings.modules = OrderedDict([
        # Core modules which shouldn't be disabled
        ("default", Storage(
            name_nice = T("Home"),
            restricted = False, # Use ACLs to control access to this module
            access = None,      # All Users (inc Anonymous) can see this module in the default menu & access the controller
            module_type = None  # This item is not shown in the menu
        )),
        ("admin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
            module_type = None  # This item is handled separately for the menu
        )),
        ("appadmin", Storage(
            name_nice = T("Administration"),
            #description = "Site Administration",
            restricted = True,
            module_type = None  # No Menu
        )),
        ("errors", Storage(
            name_nice = T("Ticket Viewer"),
            #description = "Needed for Breadcrumbs",
            restricted = False,
            module_type = None  # No Menu
        )),
        #("sync", Storage(
        #    name_nice = T("Synchronization"),
        #    #description = "Synchronization",
        #    restricted = True,
        #    access = "|1|",     # Only Administrators can see this module in the default menu & access the controller
        #    module_type = None  # This item is handled separately for the menu
        #)),
        #("tour", Storage(
        #    name_nice = T("Guided Tour Functionality"),
        #    module_type = None,
        #)),
        #("translate", Storage(
        #    name_nice = T("Translation Functionality"),
        #    #description = "Selective translation of strings based on module.",
        #    module_type = None,
        #)),
        ("gis", Storage(
            name_nice = T("Map"),
            #description = "Situation Awareness & Geospatial Analysis",
            restricted = True,
            module_type = 6,     # 6th item in the menu
        )),
        ("pr", Storage(
            name_nice = T("Person Registry"),
            #description = "Central point to record details on People",
            restricted = True,
            access = "|1|",     # Only Administrators can see this module in the default menu (access to controller is possible to all still)
            module_type = 10
        )),
        ("org", Storage(
            name_nice = T("Organizations"),
            #description = 'Lists "who is doing what & where". Allows relief agencies to coordinate their activities',
            restricted = True,
            module_type = 1
        )),
        ("hrm", Storage(
            name_nice = T("Staff"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
        )),
        ("vol", Storage(
            name_nice = T("Volunteers"),
            #description = "Human Resources Management",
            restricted = True,
            module_type = 2,
        )),
        #("cms", Storage(
        #    name_nice = T("Content Management"),
        #    #description = "Content Management System",
        #    restricted = True,
        #    module_type = 10,
        #)),
        ("doc", Storage(
            name_nice = T("Documents"),
            #description = "A library of digital resources, such as photos, documents and reports",
            restricted = True,
            module_type = 10,
        )),
        ("msg", Storage(
            name_nice = T("Messaging"),
            #description = "Sends & Receives Alerts via Email & SMS",
            restricted = True,
            # The user-visible functionality of this module isn't normally required. Rather it's main purpose is to be accessed from other modules.
            module_type = None,
        )),
        #("supply", Storage(
        #    name_nice = T("Supply Chain Management"),
        #    #description = "Used within Inventory Management, Request Management and Asset Management",
        #    restricted = True,
        #    module_type = None, # Not displayed
        #)),
        #("inv", Storage(
        #    name_nice = T("Warehouses"),
        #    #description = "Receiving and Sending Items",
        #    restricted = True,
        #    module_type = 4
        #)),
        #("asset", Storage(
        #    name_nice = T("Assets"),
        #    #description = "Recording and Assigning Assets",
        #    restricted = True,
        #    module_type = 5,
        #)),
        # Vehicle depends on Assets
        #("vehicle", Storage(
        #    name_nice = T("Vehicles"),
        #    #description = "Manage Vehicles",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("req", Storage(
        #    name_nice = T("Requests"),
        #    #description = "Manage requests for supplies, assets, staff or other resources. Matches against Inventories where supplies are requested.",
        #   restricted = True,
        #    module_type = 10,
        #)),
        #("project", Storage(
        #    name_nice = T("Projects"),
        #    #description = "Tracking of Projects, Activities and Tasks",
        #    restricted = True,
        #    module_type = 2
        #)),
        ("cr", Storage(
            name_nice = T("Camps"),
            #description = "Tracks the location, capacity and breakdown of victims in Shelters",
            restricted = True,
            module_type = 10
        )),
        #("hms", Storage(
        #    name_nice = T("Hospitals"),
        #    #description = "Helps to monitor status of hospitals",
        #    restricted = True,
        #    module_type = 10
        #)),
        ("dvr", Storage(
          name_nice = T("Case Management"),
          #description = "Allow affected individuals & households to register to receive compensation and distributions",
          restricted = True,
          module_type = 10,
        )),
        #("event", Storage(
        #    name_nice = T("Events"),
        #    #description = "Activate Events (e.g. from Scenario templates) for allocation of appropriate Resources (Human, Assets & Facilities).",
        #    restricted = True,
        #    module_type = 10,
        #)),
        #("tr", Storage(
        #   name_nice = "Turkish Extensions",
        #   restricted = True,
        #   module_type = None,
        #)),
        #("transport", Storage(
        #   name_nice = T("Transport"),
        #   restricted = True,
        #   module_type = 10,
        #)),
        ("stats", Storage(
            name_nice = T("Statistics"),
            #description = "Manages statistics",
            restricted = True,
            module_type = None,
        )),
    ])

# END =========================================================================
