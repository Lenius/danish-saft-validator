from enum import Enum


class Language(Enum):
    en = 'en'
    dk = 'dk'


class Texts:
    config_completed = {Language.en: 'Configuration file has been created.',
                        Language.dk: 'Konfigurationsfilen er oprettet.'}
    init_model = {Language.en: 'Initializing model...',
                  Language.dk: 'Initialisere modellen...'}
    model_init = {Language.en: 'Model has been initialized.',
                  Language.dk: 'Model initialiseret.'}
    path_to_xml = {Language.en: 'Input path to XML file: ',
                   Language.dk: 'Input sti til XML fil: '}
    path_not_xml_file = {Language.en: 'The specified file is not of the XML type.',
                         Language.dk: 'Den angivne fil er ikke af typen XML.'}
    path_not_exist = {Language.en: 'The specified path does not exist.',
                      Language.dk: 'Den angivne sti findes ikke.'}
    report_was_written = {Language.en: 'The report is written, do you want to delete the .xml file? yes/no: ',
                          Language.dk: 'Rapporten er skrevet, vil du slette .xml filen? ja/nej: '}
    report_was_written_delete = {
        Language.en: 'Received incorrect input; it should be yes/no. Do you want to delete the .xml file?: ',
        Language.dk: 'Modtaget forkert input; det skal være ja/nej. Vil du slette .xml filen?: '}
    errors_found = {
        Language.en: 'NOK: Errors have been found in the specified XML file. The report can be found at the following path: ',
        Language.dk: 'NOK: Fejl er fundet i den angivne XML fil. Rapporten kan findes på følgende sti: '}
    flag_errors_found = {
        Language.en: 'FLAG: Value errors have been found in the specified XML file. The report can be found at the following path: ',
        Language.dk: 'FLAG: Værdi fejl er fundet i den angivne XML fil. Rapporten kan findes på følgende sti: '}
    no_errors_found = {
        Language.en: 'OK: No errors have been found in the specified XML file. The report can be found at the following path: ',
        Language.dk: 'OK: Ingen fejl er fundet i den angivne XML fil. Rapporten kan findes på følgende sti: '}

    missing_translation_audit_trail = {Language.en: 'MISSING TRANSLATION OF AUDIT TRAIL: ',
                                       Language.dk: 'MANGLENDE OVERSÆTTELSE AF AUDIT TRAIL: '}
    yes = {Language.en: 'yes',
           Language.dk: 'ja'}
    no = {Language.en: 'no',
          Language.dk: 'nej'}
    check = {Language.en: 'Check',
             Language.dk: 'Tjek'}
    master_data = {Language.en: 'Master data',
                   Language.dk: 'Stamdata'}
    checked = {Language.en: 'Checked',
               Language.dk: 'Tjekket'}
    xml_read = {Language.en: 'Error during loading',
                Language.dk: 'Fejl ved indlæsning'}
    naming_check = {Language.en: 'Naming check',
                    Language.dk: 'Navngivningstjek'}
    structure_check = {Language.en: 'Structure check',
                       Language.dk: 'Strukturtjek'}
    certificate_check = {Language.en: 'Certificate check',
                         Language.dk: 'Certifikattjek'}
    signature_check = {Language.en: 'Signature check',
                       Language.dk: 'Signaturtjek'}
    value_check = {Language.en: 'Value check',
                       Language.dk: 'Værditjek'}
    company_name = {Language.en: 'Company name',
                    Language.dk: 'Virksomheds navn'}
    software_company_name = {Language.en: 'Software company name',
                             Language.dk: 'Software virksomheds navn'}
    software_description = {Language.en: 'Software description',
                            Language.dk: 'Software beskrivelse'}
    software_version = {Language.en: 'Software version',
                        Language.dk: 'Software version'}
    file_generated = {Language.en: 'File generated',
                      Language.dk: 'Fil genereret'}
    file_modified = {Language.en: 'File modified',
                     Language.dk: 'Fil modificeret'}
    file_last_access = {Language.en: 'Last access time',
                        Language.dk: 'Sidste adgangstidspunkt'}
    ok = {Language.en: 'OK',
          Language.dk: 'OK'}
    error = {Language.en: 'Error',
             Language.dk: 'Fejl'}
    status = {Language.en: 'Status',
              Language.dk: 'Status'}
    error_row = {Language.en: 'Error row',
                 Language.dk: 'Fejl række'}
    error_area = {Language.en: 'Error area',
                  Language.dk: 'Fejl område'}
    error_xml_element = {Language.en: 'Error XML element',
                         Language.dk: 'Fejl XML element'}
    technical_error_desc = {Language.en: 'Technical error description',
                            Language.dk: 'Teknisk fejlbeskrivelse'}
    error_desc = {Language.en: 'Error description',
                  Language.dk: 'Fejlbeskrivelse'}
