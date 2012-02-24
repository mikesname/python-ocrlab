# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Preset'
        db.create_table('ocrlab_preset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_on', self.gf('django.db.models.fields.DateField')()),
            ('updated_on', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique=True, max_length=50, populate_from=None, unique_with=(), db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('public', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('data', self.gf('ocrlab.models.jsonfield.JSONTextField')(name='data')),
            ('profile', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='presets', null=True, to=orm['ocrlab.Profile'])),
        ))
        db.send_create_signal('ocrlab', ['Preset'])

        # Adding model 'Profile'
        db.create_table('ocrlab_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_on', self.gf('django.db.models.fields.DateField')()),
            ('updated_on', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique=True, max_length=50, populate_from=None, unique_with=(), db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('data', self.gf('ocrlab.models.jsonfield.JSONTextField')(name='data')),
        ))
        db.send_create_signal('ocrlab', ['Profile'])

        # Adding model 'HelperFileApp'
        db.create_table('ocrlab_helperfileapp', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique=True, max_length=50, populate_from=None, unique_with=(), db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('ocrlab', ['HelperFileApp'])

        # Adding model 'HelperFileType'
        db.create_table('ocrlab_helperfiletype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique=True, max_length=50, populate_from=None, unique_with=(), db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('ocrlab', ['HelperFileType'])

        # Adding model 'HelperFile'
        db.create_table('ocrlab_helperfile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_on', self.gf('django.db.models.fields.DateField')()),
            ('updated_on', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('slug', self.gf('autoslug.fields.AutoSlugField')(unique=True, max_length=50, populate_from=None, unique_with=(), db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ocrlab.HelperFileType'])),
            ('app', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ocrlab.HelperFileApp'])),
        ))
        db.send_create_signal('ocrlab', ['HelperFile'])


    def backwards(self, orm):
        
        # Deleting model 'Preset'
        db.delete_table('ocrlab_preset')

        # Deleting model 'Profile'
        db.delete_table('ocrlab_profile')

        # Deleting model 'HelperFileApp'
        db.delete_table('ocrlab_helperfileapp')

        # Deleting model 'HelperFileType'
        db.delete_table('ocrlab_helperfiletype')

        # Deleting model 'HelperFile'
        db.delete_table('ocrlab_helperfile')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ocrlab.helperfile': {
            'Meta': {'object_name': 'HelperFile'},
            'app': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ocrlab.HelperFileApp']"}),
            'created_on': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '50', 'populate_from': 'None', 'unique_with': '()', 'db_index': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ocrlab.HelperFileType']"}),
            'updated_on': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        'ocrlab.helperfileapp': {
            'Meta': {'object_name': 'HelperFileApp'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '50', 'populate_from': 'None', 'unique_with': '()', 'db_index': 'True'})
        },
        'ocrlab.helperfiletype': {
            'Meta': {'object_name': 'HelperFileType'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '50', 'populate_from': 'None', 'unique_with': '()', 'db_index': 'True'})
        },
        'ocrlab.preset': {
            'Meta': {'object_name': 'Preset'},
            'created_on': ('django.db.models.fields.DateField', [], {}),
            'data': ('ocrlab.models.jsonfield.JSONTextField', [], {'name': "'data'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'profile': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'presets'", 'null': 'True', 'to': "orm['ocrlab.Profile']"}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '50', 'populate_from': 'None', 'unique_with': '()', 'db_index': 'True'}),
            'updated_on': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        'ocrlab.profile': {
            'Meta': {'object_name': 'Profile'},
            'created_on': ('django.db.models.fields.DateField', [], {}),
            'data': ('ocrlab.models.jsonfield.JSONTextField', [], {'name': "'data'"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('autoslug.fields.AutoSlugField', [], {'unique': 'True', 'max_length': '50', 'populate_from': 'None', 'unique_with': '()', 'db_index': 'True'}),
            'updated_on': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        }
    }

    complete_apps = ['ocrlab']
