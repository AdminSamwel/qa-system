/**
 * TPSC QA System — Comprehensive Bilingual Translation Engine
 * Languages: Swahili (sw) | English (en)
 * Usage: data-i18n="key"  | data-i18n-ph="key" | data-i18n-title="key"
 * Global: setLang('en') | setLang('sw') | QA.i18n.t('key')
 */
(function (root) {
    'use strict';

    const LANG_KEY    = 'qa_lang';
    const DEFAULT_LANG = 'sw';

    /* ════════════════════════════════════════════════════════════════════════
       TRANSLATION DICTIONARY
    ════════════════════════════════════════════════════════════════════════ */
    const T = {

        /* ─────────────── SWAHILI (DEFAULT) ─────────────── */
        sw: {
            /* Navigation */
            nav_brand_title:   'Chuo cha Utumishi wa Umma',
            nav_brand_sub:     'Mfumo wa Uhakika wa Ubora',
            nav_home:          'Nyumbani',
            nav_eval:          'Tathmini',
            nav_campus_reports:'Ripoti za Kampasi',
            nav_institution:   'Taasisi Nzima',
            nav_reports:       'Ripoti',
            nav_help:          'Msaada',
            nav_forms:         'Fomu',
            nav_setup:         'Mipangilio',
            nav_login:         'Ingia',
            menu_campuses:     'Kampasi',
            menu_departments:  'Idara',
            menu_programmes:   'Programu',
            menu_modules:      'Moduli',
            menu_users:        'Watumiaji',
            menu_assignments:  'Mgawanyo wa Watumiaji',
            menu_enrollments:  'Usajili',
            menu_messages:     'Ujumbe',
            menu_profile:      'Wasifu Wangu',
            menu_logout:       'Toka',

            /* Footer */
            footer_title:    'Chuo cha Utumishi wa Umma',
            footer_subtitle: 'Mfumo wa Uhakika wa Ubora',
            footer_desc:     'Kuhakikisha ubora wa elimu kupitia tathmini za kina na mfumo wa NACTVET/NAQS.',
            footer_links:    'Viungo vya Haraka',
            footer_contact:  'Mawasiliano',
            footer_rights:   'Haki zote zimehifadhiwa.',

            /* Common Buttons & Labels */
            btn_close:   'Funga',
            btn_save:    'Hifadhi',
            btn_cancel:  'Ghairi',
            btn_delete:  'Futa',
            btn_edit_lbl:'Hariri',
            btn_add:     'Ongeza',
            btn_submit:  'Wasilisha',
            btn_view:    'Angalia',
            btn_pdf:     'PDF',
            btn_csv:     'CSV',
            btn_excel:   'Excel',
            lbl_actions: 'Vitendo',
            lbl_status:  'Hali',
            lbl_no_data: 'Hakuna Data',
            lbl_loading: 'Inapakia...',
            lbl_yes:     'Ndiyo',
            lbl_no:      'Hapana',
            lbl_search:  'Tafuta',
            lbl_level:   'Kiwango',
            lbl_all:     'Zote',

            /* Table Headers (common) */
            th_code:       'Msimbo',
            th_module:     'Moduli',
            th_module_name:'Jina la Moduli',
            th_course_name:'Jina la Kozi',
            th_responses:  'Majibu',
            th_qei:        'QEI',
            th_status:     'Hali',
            th_acknowledged:'Imekubaliwa',
            th_section:    'Sehemu',
            th_ideal:      'Bora',
            th_mean:       'Wastani',
            th_criterion:  'Kigezo',
            th_naqs_ref:   'Rejeleo la NAQS',
            th_score:      'Alama',
            th_threshold:  'Kizingiti',
            th_action:     'Hatua',
            th_campus:     'Kampasi',
            th_lecturer:   'Mkufunzi',
            th_programme:  'Programu',
            th_semester:   'Semester',
            th_year:       'Mwaka',
            th_role:       'Jukumu',
            th_email:      'Barua Pepe',
            th_date:       'Tarehe',
            th_form:       'Fomu',
            th_sections:   'Sehemu',
            th_questions:  'Maswali',
            th_created:    'Imeundwa',
            th_type:       'Aina',
            th_facilitator:'Mkufunzi/Mwezeshaji',

            /* QEI Status Labels */
            qei_excellent:        'Bora',
            qei_satisfactory:     'Inaridhisha',
            qei_needs_improvement:'Inahitaji Uboreshaji',
            qei_unsatisfactory:   'Hairidhishi',
            qei_no_data:          'Hakuna Data',
            qei_compliant:        'Inastahili',
            qei_non_compliant:    'Haistahili',
            qei_formula_note:     'QEI = Wastani wa Alama / Alama Bora (5.0)',

            /* QEI Scale Legend */
            scale_title:        'Kumbukumbu ya Kiwango cha QEI (NACTVET)',
            scale_excellent:    '≥ 0.80 — Bora',
            scale_satisfactory: '≥ 0.60 — Inaridhisha (Inastahili)',
            scale_needs_imp:    '≥ 0.40 — Inahitaji Uboreshaji',
            scale_unsatisf:     '< 0.40 — Hairidhishi',
            scale_formula:      'QEI = Wastani wa Alama / Alama Bora (5.0)',

            /* Acknowledgement Badges */
            badge_acknowledged: 'Imekubaliwa',
            badge_pending:      'Inasubiri',
            badge_action_req:   'Hatua Inahitajika',

            /* ── Director Dashboard ── */
            dir_title:            'Bodi ya Mkurugenzi',
            dir_subtitle:         'Muhtasari wa QEI kwa Kampasi',
            lbl_campus_qei:       'QEI ya Kampasi',
            lbl_total_courses:    'Jumla ya Kozi',
            lbl_total_evals:      'Jumla ya Tathmini',
            lbl_below_threshold:  'Kozi Chini ya Kizingiti cha 60%',
            lbl_action_required:  'Hatua Inahitajika',
            lbl_course_qei_summ:  'Muhtasari wa QEI za Kozi',
            lbl_qei_scale:        'Kiwango cha QEI',
            lbl_pdf_report:       'Ripoti ya PDF',
            lbl_following_courses:'Kozi zifuatazo zina QEI chini ya kizingiti cha 60%:',
            btn_view_report:      'Angalia Ripoti',
            btn_view_detail:      'Ripoti Kamili',
            btn_nactvet_report:   'Ripoti ya NACTVET QEI',
            btn_ack_report:       'Kubali Ripoti',
            btn_update_ack:       'Sasisha Ukubaliaji',
            lbl_no_courses:       'Hakuna kozi zilizopatikana kwa kampasi hii.',

            /* ── CEO Dashboard ── */
            ceo_title:              'Muhtasari wa Taasisi — Bodi ya CEO',
            ceo_subtitle:           'Faharasa ya Ufanisi wa Ubora (QEI) kwa Kampasi Zote',
            lbl_institution_qei:    'QEI ya Taasisi',
            lbl_inst_performance:   'Utendaji wa jumla wa taasisi',
            lbl_campuses:           'Kampasi',
            lbl_active_branches:    'Kampasi/matawi yanayofanya kazi',
            lbl_below_threshold_c:  'Kampasi Chini ya Kizingiti',
            lbl_qei_action:         'QEI < 0.60 (hatua inahitajika)',
            lbl_courses:            'Kozi',
            lbl_evaluations:        'Tathmini',
            lbl_below_thr_label:    'Chini ya Kizingiti',
            lbl_no_courses_campus:  'Hakuna kozi zilizopatikana kwa kampasi hii.',

            /* Acknowledge Modal */
            modal_ack_dir:    'Ukubaliaji wa Ripoti',
            modal_ack_ceo:    'Ukubaliaji wa CEO',
            modal_module:     'Moduli',
            modal_qei_lbl:    'QEI',
            modal_campus:     'Kampasi',
            modal_no_data:    'Hakuna data',
            modal_notes_lbl:  'Maoni / Maelekezo (Notes / Directives)',
            modal_notes_ph:   'Andika maoni, maelekezo, au hatua zinazohitajika...',
            modal_action_lbl: 'Weka alama ya hatua ya taasisi inayohitajika',
            modal_action_ceo: 'Weka alama ya hatua ya taasisi inayohitajika',
            modal_ack_on:     'Imekubaliwa tarehe',
            btn_ack_save:     'Kubali',
            btn_dir_save_ack: 'Hifadhi Ukubaliaji',

            /* ── Course Report ── */
            cr_avg_score:        'Wastani wa Alama',
            cr_qei_score:        'Alama ya QEI',
            cr_total_responses:  'Jumla ya Majibu',
            cr_lecturer:         'Mkufunzi',
            cr_out_of_5:         'kati ya 5',
            cr_nactvet_badge:    'Uzingatifu wa NACTVET',
            cr_full_nactvet:     'Ripoti Kamili ya NACTVET →',
            cr_criteria_met:     'vigezo vimekutana',
            cr_qual_title:       'Uchambuzi wa Ubora — Sauti ya Mwanafunzi',
            cr_sentiment_title:  'Mgawanyo wa Hisia',
            cr_responses_ana:    'majibu ya wazi yaliyochambuliwa',
            cr_pos_label:        'Chanya',
            cr_neu_label:        'Wastani',
            cr_cons_label:       'Ujenzi',
            cr_themes_title:     'Mada Zilizotambuliwa',
            cr_themes_desc:      'Mada zilizopatikana kutoka majibu ya wazi, zimewekwa kwa viwango vya NAQS',
            cr_pos_feedback:     'Maoni Mazuri ya Wanafunzi',
            cr_cons_feedback:    'Maoni ya Ujenzi',
            cr_pos_lbl:          'chanya',
            cr_cons_lbl:         'ujenzi',
            cr_mixed_title:      'Uchambuzi wa Njia Mchanganyiko na Mapendekezo',
            cr_mixed_desc:       'Mapendekezo yafuatayo yanazalishwa kwa kuunganisha alama za QEI na mada za maoni ya ubora ya wanafunzi, yakioanishwa na viwango vya NACTVET.',
            cr_priority_crit:    'MUHIMU SANA',
            cr_priority_high:    'JUU',
            cr_priority_med:     'KATI',
            cr_priority_maint:   'KUDUMISHA',
            cr_triangulated:     'Imeunganishwa',
            cr_quant_ev:         'Ushahidi wa Kiidadi',
            cr_qual_ev:          'Ushahidi wa Ubora',
            cr_rec_action:       'Hatua Inayopendekezwa',
            cr_exp_outcome:      'Matokeo Yanayotarajiwa',
            cr_mentions:         'matukio',
            cr_ack_section:      'Ukubaliaji wa Ripoti (Acknowledgements)',
            cr_no_comments:      'Hakuna maoni yaliyoandikwa.',

            /* ── QEI Report ── */
            qei_overall:         'QEI ya Jumla',
            qei_mean:            'Wastani wa Alama',
            qei_responses:       'Majibu',
            qei_compliance:      'Uzingatifu wa NACTVET',
            qei_submitted:       'tathmini zilizowasilishwa',
            qei_out_of:          'kati ya 5.00',
            qei_criteria_title:  'Vigezo vya Tathmini ya NACTVET — Kifungu 3.5',
            qei_criteria_met:    'vigezo vimekutana',
            qei_thr_label:       'Kizingiti: 60%',
            qei_sec_breakdown:   'Mgawanyo wa QEI kwa Sehemu',
            qei_strengths:       'Nguvu (Wastani ≥ 4.0)',
            qei_weaknesses:      'Maeneo Yanayohitaji Uboreshaji (Wastani ≤ 2.5)',
            qei_insights_title:  'Maarifa ya QA',
            qei_prediction_lbl:  'Utabiri',
            qei_mixed_title:     'Uchambuzi wa Njia Mchanganyiko na Mapendekezo',
            qei_voice_sentiment: 'Hisia za Sauti ya Mwanafunzi',
            qei_top_themes:      'Mada Kuu Zilizotambuliwa',
            qei_comments_ana:    'maoni yaliyochambuliwa',
            qei_priority_col:    'Kipaumbele',
            qei_area_col:        'Eneo la Wasiwasi / Nguvu',
            qei_finding_col:     'Matokeo ya Kiidadi',
            qei_rec_col:         'Hatua Inayopendekezwa',
            qei_footnote:        'Uzingatifu = QEI ya kigezo ≥ kizingiti (0.60).',
            qei_full_link:       'Angalia uchambuzi kamili wa ubora katika Ripoti ya Kozi →',
            qei_naqs_std:        'Kumbukumbu ya Viwango vya NAQS',
            qei_full_report:     'Ripoti Kamili',
            qei_pdf_btn:         'PDF',
            qei_trig_label:      'Imeunganishwa',

            /* ── Public Evaluation Form ── */
            pf_title_label:    'Tathmini ya Kozi',
            pf_evaluating:     'Unayemtathmini',
            pf_scale_title:    'Mwongozo wa Kipimo:',
            pf_scale_1:        '1 = Sikubaliani Kabisa',
            pf_scale_2:        '2 = Sikubaliani',
            pf_scale_3:        '3 = Wastani',
            pf_scale_4:        '4 = Nakubaliana',
            pf_scale_5:        '5 = Nakubaliana Kabisa',
            pf_required:       '* Inahitajika',
            pf_submit:         'Wasilisha Tathmini',
            pf_submitting:     'Inawasilisha...',
            pf_prev:           'Nyuma',
            pf_next:           'Mbele',
            pf_of:             'ya',
            pf_section:        'Sehemu',
            pf_your_answer:    'Jibu lako...',
            pf_select_one:     'Chagua jibu moja',
            pf_strongly_dis:   'Sikubaliani Kabisa',
            pf_disagree:       'Sikubaliani',
            pf_neutral:        'Wastani',
            pf_agree:          'Nakubaliana',
            pf_strongly_agree: 'Nakubaliana Kabisa',
            pf_anonymous_note: 'Tathmini hii ni ya siri na ya kujitegemea.',
            pf_lang_label:     'Lugha / Language',

            /* ── Evaluation List ── */
            eval_title:        'Kozi Zinazopatikana kwa Tathmini',
            eval_no_courses:   'Hujasajiliwa katika kozi yoyote. Wasiliana na utawala.',
            eval_no_avail:     'Hakuna kozi zinazopatikana.',
            eval_evaluated:    'Tathmini Imefanywa',
            eval_pending:      'Inasubiri',
            eval_start:        'Anza Tathmini',
            eval_view_report:  'Angalia Ripoti',
            eval_view_sub:     'Angalia Uwasilishaji',
            lbl_level:         'Kiwango',

            /* ── Forms Manager ── */
            fm_templates_hd:   'Templeti za Fomu',
            fm_active_hd:      'Fomu Zinazotumika',
            fm_clone_btn:      'Nakili na Hariri',
            fm_preview_btn:    'Hakiki',
            fm_edit_btn:       'Hariri',
            fm_toggle_btn:     'Washa/Zima',
            fm_qs_count:       'maswali',
            fm_sec_count:      'sehemu',
            fm_no_templates:   'Hakuna templeti.',
            fm_no_forms:       'Hakuna fomu. Unda ya kwanza.',
            fm_form_type:      'Aina',
            fm_created_lbl:    'Imeundwa',
            fm_active_badge:   'Inafanya kazi',
            fm_inactive_badge: 'Imezimwa',
            fm_new_form:       'Fomu Mpya',

            /* ── Admin Courses ── */
            adm_courses_title: 'Usimamizi wa Kozi / Moduli',
            adm_add_course:    'Ongeza Kozi',
            adm_no_courses:    'Hakuna kozi zilizopatikana.',
            adm_linked_form:   'Fomu',
            adm_no_form:       'Hakuna Fomu',
            adm_evals:         'Tathmini',

            /* ── Auth / Login ── */
            auth_welcome:     'Karibu Tena',
            auth_sub:         'Ingia kwenye akaunti yako ya Mfumo wa QA',
            auth_username:    'Jina la Mtumiaji',
            auth_password:    'Nywila',
            auth_login_btn:   'Ingia',
            auth_forgot:      'Umesahau nywila? Wasiliana na',
            auth_qa_office:   'Ofisi ya QA',
            auth_college:     'Chuo cha Utumishi wa Umma Tanzania',
            auth_tagline:     'Kuhakikisha ubora wa elimu kupitia tathmini endelevu na uboreshaji katika kampasi zote.',
            auth_feat1:       'Tathmini Zinazozingatia Sera ya NACTVET',
            auth_feat2:       'Ripoti za Kielezo cha Ufanisi wa Ubora (QEI)',
            auth_feat3:       'Kampasi Nyingi — Wanafunzi & Watumishi wa Umma',
            auth_feat4:       'Ripoti za Kiotomatiki za Uzingatiaji wa NACTVET',
            auth_footer:      'Mfumo wa Udhibiti wa Ubora',
        },

        /* ─────────────── ENGLISH ─────────────── */
        en: {
            /* Navigation */
            nav_brand_title:   'Tanzania Public Service College',
            nav_brand_sub:     'Quality Assurance System',
            nav_home:          'Home',
            nav_eval:          'Evaluations',
            nav_campus_reports:'Campus Reports',
            nav_institution:   'Institution Overview',
            nav_reports:       'Reports',
            nav_help:          'Help',
            nav_forms:         'Forms',
            nav_setup:         'Settings',
            nav_login:         'Login',
            menu_campuses:     'Campuses',
            menu_departments:  'Departments',
            menu_programmes:   'Programmes',
            menu_modules:      'Modules',
            menu_users:        'Users',
            menu_assignments:  'User Assignments',
            menu_enrollments:  'Enrollments',
            menu_messages:     'Messages',
            menu_profile:      'My Profile',
            menu_logout:       'Logout',

            /* Footer */
            footer_title:    'Tanzania Public Service College',
            footer_subtitle: 'Quality Assurance System',
            footer_desc:     'Ensuring quality education through comprehensive evaluations and the NACTVET/NAQS framework.',
            footer_links:    'Quick Links',
            footer_contact:  'Contact',
            footer_rights:   'All rights reserved.',

            /* Common */
            btn_close:   'Close',
            btn_save:    'Save',
            btn_cancel:  'Cancel',
            btn_delete:  'Delete',
            btn_edit_lbl:'Edit',
            btn_add:     'Add',
            btn_submit:  'Submit',
            btn_view:    'View',
            btn_pdf:     'PDF',
            btn_csv:     'CSV',
            btn_excel:   'Excel',
            lbl_actions: 'Actions',
            lbl_status:  'Status',
            lbl_no_data: 'No Data',
            lbl_loading: 'Loading...',
            lbl_yes:     'Yes',
            lbl_no:      'No',
            lbl_search:  'Search',
            lbl_level:   'Level',
            lbl_all:     'All',

            /* Table Headers */
            th_code:       'Code',
            th_module:     'Module',
            th_module_name:'Module Name',
            th_course_name:'Course Name',
            th_responses:  'Responses',
            th_qei:        'QEI',
            th_status:     'Status',
            th_acknowledged:'Acknowledged',
            th_section:    'Section',
            th_ideal:      'Ideal',
            th_mean:       'Mean',
            th_criterion:  'Criterion',
            th_naqs_ref:   'NAQS Reference',
            th_score:      'Score',
            th_threshold:  'Threshold',
            th_action:     'Action',
            th_campus:     'Campus',
            th_lecturer:   'Lecturer',
            th_programme:  'Programme',
            th_semester:   'Semester',
            th_year:       'Year',
            th_role:       'Role',
            th_email:      'Email',
            th_date:       'Date',
            th_form:       'Form',
            th_sections:   'Sections',
            th_questions:  'Questions',
            th_created:    'Created',
            th_type:       'Type',
            th_facilitator:'Facilitator / Lecturer',

            /* QEI Status */
            qei_excellent:        'Excellent',
            qei_satisfactory:     'Satisfactory',
            qei_needs_improvement:'Needs Improvement',
            qei_unsatisfactory:   'Unsatisfactory',
            qei_no_data:          'No Data',
            qei_compliant:        'Compliant',
            qei_non_compliant:    'Non-Compliant',
            qei_formula_note:     'QEI = Mean Score / Ideal Score (5.0)',

            /* QEI Scale Legend */
            scale_title:        'QEI Scale Reference (NACTVET Standard)',
            scale_excellent:    '≥ 0.80 — Excellent',
            scale_satisfactory: '≥ 0.60 — Satisfactory (Compliant)',
            scale_needs_imp:    '≥ 0.40 — Needs Improvement',
            scale_unsatisf:     '< 0.40 — Unsatisfactory',
            scale_formula:      'QEI = Mean Score / Ideal Score (5.0)',

            /* Acknowledgement Badges */
            badge_acknowledged: 'Acknowledged',
            badge_pending:      'Pending',
            badge_action_req:   'Action Required',

            /* ── Director Dashboard ── */
            dir_title:            'Director Dashboard',
            dir_subtitle:         'Quality Effectiveness Index (QEI) overview for your campus',
            lbl_campus_qei:       'Campus QEI',
            lbl_total_courses:    'Total Courses',
            lbl_total_evals:      'Total Evaluations',
            lbl_below_threshold:  'Courses Below 60% QEI',
            lbl_action_required:  'Action Required',
            lbl_course_qei_summ:  'Course QEI Summary',
            lbl_qei_scale:        'QEI Scale',
            lbl_pdf_report:       'PDF Report',
            lbl_following_courses:'The following courses have a QEI below the 60% threshold:',
            btn_view_report:      'View Report',
            btn_view_detail:      'Detailed Report',
            btn_nactvet_report:   'NACTVET QEI Report',
            btn_ack_report:       'Acknowledge Report',
            btn_update_ack:       'Update Acknowledgement',
            lbl_no_courses:       'No courses found for this campus.',

            /* ── CEO Dashboard ── */
            ceo_title:              'Institutional Overview — CEO Dashboard',
            ceo_subtitle:           'Quality Effectiveness Index (QEI) across all campuses — NACTVET Compliance View',
            lbl_institution_qei:    'Institution QEI',
            lbl_inst_performance:   'Overall institutional performance',
            lbl_campuses:           'Campuses',
            lbl_active_branches:    'Active campuses / branches',
            lbl_below_threshold_c:  'Campuses Below Threshold',
            lbl_qei_action:         'QEI < 0.60 (action required)',
            lbl_courses:            'Courses',
            lbl_evaluations:        'Evaluations',
            lbl_below_thr_label:    'Below Threshold',
            lbl_no_courses_campus:  'No courses found for this campus.',

            /* Acknowledge Modal */
            modal_ack_dir:    'Report Acknowledgement',
            modal_ack_ceo:    'CEO Acknowledgement',
            modal_module:     'Module',
            modal_qei_lbl:    'QEI',
            modal_campus:     'Campus',
            modal_no_data:    'No data',
            modal_notes_lbl:  'Notes / Directives',
            modal_notes_ph:   'Write notes, directives, or required actions...',
            modal_action_lbl: 'Flag for follow-up action',
            modal_action_ceo: 'Flag for institutional action required',
            modal_ack_on:     'Acknowledged on',
            btn_ack_save:     'Acknowledge',
            btn_dir_save_ack: 'Save Acknowledgement',

            /* ── Course Report ── */
            cr_avg_score:        'Average Score',
            cr_qei_score:        'QEI Score',
            cr_total_responses:  'Total Responses',
            cr_lecturer:         'Lecturer',
            cr_out_of_5:         'out of 5',
            cr_nactvet_badge:    'NACTVET Compliance',
            cr_full_nactvet:     'Full NACTVET Report →',
            cr_criteria_met:     'criteria met',
            cr_qual_title:       'Qualitative Analysis — Student Voice',
            cr_sentiment_title:  'Sentiment Distribution',
            cr_responses_ana:    'open-ended responses analysed',
            cr_pos_label:        'Positive',
            cr_neu_label:        'Neutral',
            cr_cons_label:       'Constructive',
            cr_themes_title:     'Identified Themes',
            cr_themes_desc:      'Themes extracted from student open-ended responses, mapped to NAQS standards',
            cr_pos_feedback:     'Positive Student Feedback',
            cr_cons_feedback:    'Constructive Feedback',
            cr_pos_lbl:          'positive',
            cr_cons_lbl:         'constructive',
            cr_mixed_title:      'Mixed Methods Analysis & Recommendations',
            cr_mixed_desc:       'The following recommendations are generated by triangulating quantitative QEI scores with qualitative student feedback themes, aligned to NACTVET quality standards.',
            cr_priority_crit:    'CRITICAL',
            cr_priority_high:    'HIGH',
            cr_priority_med:     'MEDIUM',
            cr_priority_maint:   'MAINTAIN',
            cr_triangulated:     'Triangulated',
            cr_quant_ev:         'Quantitative Evidence',
            cr_qual_ev:          'Qualitative Evidence',
            cr_rec_action:       'Recommended Action',
            cr_exp_outcome:      'Expected Outcome',
            cr_mentions:         'mentions',
            cr_ack_section:      'Report Acknowledgements',
            cr_no_comments:      'No notes written.',

            /* ── QEI Report ── */
            qei_overall:         'Overall QEI',
            qei_mean:            'Mean Score',
            qei_responses:       'Responses',
            qei_compliance:      'NACTVET Compliance',
            qei_submitted:       'evaluations submitted',
            qei_out_of:          'out of 5.00',
            qei_criteria_title:  'NACTVET Assessment Criteria — Section 3.5',
            qei_criteria_met:    'criteria met',
            qei_thr_label:       'Threshold: 60%',
            qei_sec_breakdown:   'Section QEI Breakdown',
            qei_strengths:       'Strengths (Mean ≥ 4.0)',
            qei_weaknesses:      'Areas Needing Improvement (Mean ≤ 2.5)',
            qei_insights_title:  'QA Insights',
            qei_prediction_lbl:  'Prediction',
            qei_mixed_title:     'Mixed Methods Analysis & Recommendations',
            qei_voice_sentiment: 'Student Voice Sentiment',
            qei_top_themes:      'Top Themes Identified',
            qei_comments_ana:    'comments analysed',
            qei_priority_col:    'Priority',
            qei_area_col:        'Area of Concern / Strength',
            qei_finding_col:     'Quantitative Finding',
            qei_rec_col:         'Recommended Action',
            qei_footnote:        'Compliance = criterion QEI ≥ threshold (0.60).',
            qei_full_link:       'View full qualitative analysis in Course Report →',
            qei_naqs_std:        'NAQS Standards Reference',
            qei_full_report:     'Full Report',
            qei_pdf_btn:         'PDF',
            qei_trig_label:      'Triangulated',

            /* ── Public Evaluation Form ── */
            pf_title_label:    'Course Evaluation',
            pf_evaluating:     'Evaluating Lecturer',
            pf_scale_title:    'Rating Scale Guide:',
            pf_scale_1:        '1 = Strongly Disagree',
            pf_scale_2:        '2 = Disagree',
            pf_scale_3:        '3 = Neutral',
            pf_scale_4:        '4 = Agree',
            pf_scale_5:        '5 = Strongly Agree',
            pf_required:       '* Required',
            pf_submit:         'Submit Evaluation',
            pf_submitting:     'Submitting...',
            pf_prev:           'Previous',
            pf_next:           'Next',
            pf_of:             'of',
            pf_section:        'Section',
            pf_your_answer:    'Your answer...',
            pf_select_one:     'Select one answer',
            pf_strongly_dis:   'Strongly Disagree',
            pf_disagree:       'Disagree',
            pf_neutral:        'Neutral',
            pf_agree:          'Agree',
            pf_strongly_agree: 'Strongly Agree',
            pf_anonymous_note: 'This evaluation is confidential and anonymous.',
            pf_lang_label:     'Lugha / Language',

            /* ── Evaluation List ── */
            eval_title:        'Courses Available for Evaluation',
            eval_no_courses:   'You are not enrolled in any courses. Please contact administration.',
            eval_no_avail:     'No courses available.',
            eval_evaluated:    'Evaluated',
            eval_pending:      'Pending',
            eval_start:        'Start Evaluation',
            eval_view_report:  'View Report',
            eval_view_sub:     'View Your Submission',

            /* ── Forms Manager ── */
            fm_templates_hd:   'Form Templates',
            fm_active_hd:      'Active Forms',
            fm_clone_btn:      'Clone & Edit',
            fm_preview_btn:    'Preview',
            fm_edit_btn:       'Edit',
            fm_toggle_btn:     'Toggle',
            fm_qs_count:       'questions',
            fm_sec_count:      'sections',
            fm_no_templates:   'No templates.',
            fm_no_forms:       'No forms yet. Create the first one.',
            fm_form_type:      'Type',
            fm_created_lbl:    'Created',
            fm_active_badge:   'Active',
            fm_inactive_badge: 'Inactive',
            fm_new_form:       'New Form',

            /* ── Admin Courses ── */
            adm_courses_title: 'Course / Module Management',
            adm_add_course:    'Add Course',
            adm_no_courses:    'No courses found.',
            adm_linked_form:   'Form',
            adm_no_form:       'No Form',
            adm_evals:         'Evaluations',

            /* ── Auth / Login ── */
            auth_welcome:     'Welcome Back',
            auth_sub:         'Sign in to your QA System account',
            auth_username:    'Username',
            auth_password:    'Password',
            auth_login_btn:   'Sign In',
            auth_forgot:      'Forgot password? Contact the',
            auth_qa_office:   'QA Office',
            auth_college:     'Tanzania Public Service College',
            auth_tagline:     'Ensuring quality education through continuous evaluation and improvement across all campuses.',
            auth_feat1:       'NACTVET Policy Compliant Evaluations',
            auth_feat2:       'Quality Effectiveness Index (QEI) Reports',
            auth_feat3:       'Multi-Campus — Students & Public Servants',
            auth_feat4:       'Automated NACTVET Compliance Reports',
            auth_footer:      'Quality Assurance System',
        },
    };

    /* ════════════════════════════════════════════════════════════════════════
       ENGINE
    ════════════════════════════════════════════════════════════════════════ */

    function getLang() {
        return localStorage.getItem(LANG_KEY) || DEFAULT_LANG;
    }

    function t(key, fallback) {
        var lang = getLang();
        var dict = T[lang] || T[DEFAULT_LANG];
        return dict[key] !== undefined ? dict[key] : (fallback !== undefined ? fallback : key);
    }

    function applyTranslations(lang) {
        lang = lang || getLang();
        var dict = T[lang] || T[DEFAULT_LANG];

        /* data-i18n → textContent */
        document.querySelectorAll('[data-i18n]').forEach(function (el) {
            var key = el.getAttribute('data-i18n');
            if (dict[key] !== undefined) el.textContent = dict[key];
        });

        /* data-i18n-html → innerHTML (for content with embedded HTML entities) */
        document.querySelectorAll('[data-i18n-html]').forEach(function (el) {
            var key = el.getAttribute('data-i18n-html');
            if (dict[key] !== undefined) el.innerHTML = dict[key];
        });

        /* data-i18n-ph → placeholder */
        document.querySelectorAll('[data-i18n-ph]').forEach(function (el) {
            var key = el.getAttribute('data-i18n-ph');
            if (dict[key] !== undefined) el.placeholder = dict[key];
        });

        /* data-i18n-title → title attribute */
        document.querySelectorAll('[data-i18n-title]').forEach(function (el) {
            var key = el.getAttribute('data-i18n-title');
            if (dict[key] !== undefined) el.title = dict[key];
        });

        /* data-i18n-aria → aria-label */
        document.querySelectorAll('[data-i18n-aria]').forEach(function (el) {
            var key = el.getAttribute('data-i18n-aria');
            if (dict[key] !== undefined) el.setAttribute('aria-label', dict[key]);
        });

        /* Update <html lang> */
        document.documentElement.lang = lang;

        /* Update language switcher buttons (any element with data-lang-btn="xx") */
        document.querySelectorAll('[data-lang-btn]').forEach(function (btn) {
            btn.classList.toggle('active', btn.getAttribute('data-lang-btn') === lang);
        });

        /* Dispatch event so page-level handlers can react */
        try {
            document.dispatchEvent(new CustomEvent('qa:langchange', { detail: { lang: lang } }));
        } catch (e) { /* IE compat */ }
    }

    function setLang(lang) {
        localStorage.setItem(LANG_KEY, lang);
        applyTranslations(lang);
    }

    /* Auto-apply on DOM ready */
    function init() { applyTranslations(getLang()); }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    /* ── Public API ── */
    root.QA       = root.QA || {};
    root.QA.i18n  = { t: t, setLang: setLang, getLang: getLang, apply: applyTranslations };
    root.setLang  = setLang;          /* global shortcut used in onclick handlers */
    root.t        = t;                /* global shortcut for inline use */

}(window));
