import os
from pathlib import Path


class FileSystem:
    __CODE_FOLDER = Path(os.path.dirname(os.path.realpath(__file__)) + '/../../')
    templates = __CODE_FOLDER / 'templates'
    saf_t_xsd = templates / 'SAF-T.xsd'
    audit_trail = __CODE_FOLDER / 'templates' / 'audit_trail.xlsx'
    error_types = __CODE_FOLDER / 'templates' / 'error_types.xlsx'
    trusted_certificates_dir = __CODE_FOLDER / 'templates' / 'approved_root_certificates'
    config = __CODE_FOLDER / 'config.ini'
    modules = __CODE_FOLDER / 'modules'
    conventions = modules / 'conventions'
