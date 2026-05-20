from sqlalchemy.orm import Session
from db.models import AppSetting

def get_settings(db: Session):
    settings = db.query(AppSetting).all()
    return {setting.key: setting.value for setting in settings}

def update_settings(db: Session, settings_data: dict):
    updated = {}
    for key, value in settings_data.items():
        setting = db.query(AppSetting).filter(AppSetting.key == key).first()
        if setting:
            setting.value = str(value)
        else:
            new_setting = AppSetting(key=key, value=str(value))
            db.add(new_setting)
        updated[key] = value
    
    db.commit()
    return get_settings(db)
