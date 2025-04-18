# Generated by Django 5.1.8 on 2025-04-16 07:11

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, help_text='Name of the category', max_length=100, unique=True)),
                ('slug', models.SlugField(help_text='URL-friendly version of the category name', unique=True)),
                ('description', models.TextField(blank=True, help_text='Brief description of the category')),
                ('order', models.PositiveIntegerField(default=0, help_text='Display order of the category')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent', models.ForeignKey(blank=True, help_text='Parent category if this is a subcategory', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subcategories', to='news.category')),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(db_index=True, help_text='Title of the article', max_length=200)),
                ('slug', models.SlugField(help_text='URL-friendly version of the title', max_length=255, unique=True)),
                ('content', models.TextField(help_text='Main content of the article')),
                ('excerpt', models.TextField(blank=True, help_text='Short summary of the article')),
                ('featured_image', models.ImageField(blank=True, help_text='Main image for the article', null=True, upload_to='news/images/%Y/%m/')),
                ('featured_image_caption', models.CharField(blank=True, help_text='Caption for the featured image', max_length=255)),
                ('meta_description', models.CharField(blank=True, help_text='Description for search engines (max 160 characters)', max_length=160)),
                ('meta_keywords', models.CharField(blank=True, help_text='Keywords for search engines (comma-separated)', max_length=255)),
                ('is_published', models.BooleanField(db_index=True, default=False, help_text='Whether the article is publicly visible')),
                ('is_featured', models.BooleanField(db_index=True, default=False, help_text='Whether to feature this article on the homepage')),
                ('is_breaking', models.BooleanField(db_index=True, default=False, help_text='Whether this is breaking news')),
                ('published_date', models.DateTimeField(blank=True, db_index=True, help_text='When the article was/will be published', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('view_count', models.PositiveIntegerField(default=0, help_text='Number of times this article has been viewed')),
                ('social_title', models.CharField(blank=True, help_text='Alternative title for social media sharing', max_length=100)),
                ('social_description', models.TextField(blank=True, help_text='Alternative description for social media sharing')),
                ('social_image', models.ImageField(blank=True, help_text='Alternative image for social media sharing', null=True, upload_to='news/social/%Y/%m/')),
                ('author', models.ForeignKey(help_text='User who wrote the article', on_delete=django.db.models.deletion.CASCADE, related_name='articles', to=settings.AUTH_USER_MODEL)),
                ('related_articles', models.ManyToManyField(blank=True, help_text='Other articles related to this one', related_name='related_to', to='news.article')),
                ('categories', models.ManyToManyField(blank=True, help_text='Categories this article belongs to', related_name='articles', to='news.category')),
            ],
            options={
                'verbose_name': 'Article',
                'verbose_name_plural': 'Articles',
                'ordering': ['-is_featured', '-published_date'],
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(help_text='Content of the comment')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_approved', models.BooleanField(db_index=True, default=False, help_text='Whether the comment is approved and visible')),
                ('article', models.ForeignKey(help_text='Article being commented on', on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='news.article')),
                ('author', models.ForeignKey(help_text='User who wrote the comment', on_delete=django.db.models.deletion.CASCADE, related_name='news_comments', to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(blank=True, help_text='Parent comment if this is a reply', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='news.comment')),
            ],
            options={
                'verbose_name': 'Comment',
                'verbose_name_plural': 'Comments',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, help_text='Name of the tag', max_length=50, unique=True)),
                ('slug', models.SlugField(help_text='URL-friendly version of the tag name', unique=True)),
                ('description', models.TextField(blank=True, help_text='Brief description of what this tag represents')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
                'ordering': ['name'],
                'indexes': [models.Index(fields=['slug'], name='news_tag_slug_4142b7_idx')],
            },
        ),
        migrations.AddField(
            model_name='article',
            name='tags',
            field=models.ManyToManyField(blank=True, help_text='Tags associated with this article', related_name='articles', to='news.tag'),
        ),
        migrations.CreateModel(
            name='ArticleView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(blank=True, help_text='Session ID for anonymous users', max_length=40, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of the viewer', null=True)),
                ('user_agent', models.TextField(blank=True, help_text="User agent string from the viewer's browser")),
                ('device_type', models.CharField(blank=True, help_text='Type of device (desktop, mobile, tablet, etc.)', max_length=20)),
                ('browser', models.CharField(blank=True, help_text='Browser used to view the article', max_length=50)),
                ('os', models.CharField(blank=True, help_text='Operating system of the viewer', max_length=50)),
                ('referrer', models.URLField(blank=True, help_text='URL that referred the viewer to this article', max_length=500)),
                ('time_spent', models.PositiveIntegerField(blank=True, help_text='Time spent viewing the article in seconds', null=True)),
                ('viewed_at', models.DateTimeField(auto_now_add=True, db_index=True, help_text='When the article was viewed')),
                ('article', models.ForeignKey(help_text='The article that was viewed', on_delete=django.db.models.deletion.CASCADE, related_name='views', to='news.article')),
                ('user', models.ForeignKey(blank=True, help_text='The user who viewed the article (if authenticated)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='article_views', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Article View',
                'verbose_name_plural': 'Article Views',
                'ordering': ['-viewed_at'],
                'indexes': [models.Index(fields=['article', '-viewed_at'], name='news_articl_article_3ee57b_idx'), models.Index(fields=['user', '-viewed_at'], name='news_articl_user_id_2f3925_idx'), models.Index(fields=['session_id'], name='news_articl_session_2b2a95_idx'), models.Index(fields=['ip_address'], name='news_articl_ip_addr_07c49e_idx'), models.Index(fields=['device_type'], name='news_articl_device__6d19c4_idx')],
            },
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['slug'], name='news_catego_slug_0c9c67_idx'),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['parent'], name='news_catego_parent__52eccc_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['article', '-created_at'], name='news_commen_article_c962b8_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['author'], name='news_commen_author__e96fd0_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['parent'], name='news_commen_parent__f18116_idx'),
        ),
        migrations.AddIndex(
            model_name='comment',
            index=models.Index(fields=['is_approved'], name='news_commen_is_appr_67abdb_idx'),
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['-published_date'], name='news_articl_publish_2bbbd4_idx'),
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['slug'], name='news_articl_slug_869c04_idx'),
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['author'], name='news_articl_author__94d1eb_idx'),
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['is_published', '-published_date'], name='news_articl_is_publ_3046c8_idx'),
        ),
        migrations.AddIndex(
            model_name='article',
            index=models.Index(fields=['is_featured', '-published_date'], name='news_articl_is_feat_128181_idx'),
        ),
    ]
