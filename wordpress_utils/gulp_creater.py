'''
Creates a gulp file for a sebodev project

arg1: the theme directory on the webfaction server
arg2: a local destination to save the gulp file to
'''
import sys, os.path

theme_dir = sys.argv[1]
js_dir = theme_dir + '/js'
save_dir = sys.argv[2]

gulp_file_contents = """
var gulp = require('gulp');
var sass = require('gulp-ruby-sass');
var sftp = require('gulp-sftp');
var plumber = require('gulp-plumber');
var autoprefixer = require('gulp-autoprefixer');
var csscomb = require('gulp-csscomb');
var combineMediaQueries = require('gulp-combine-media-queries');
var plugins = require( 'gulp-load-plugins' )({ camelize: true });
var concat = require('gulp-concat');
var rename = require('gulp-rename');
var uglify = require('gulp-uglify');

var dir = {
    sass: './sass/',
    img: './img/',
    js: './js/',
    bower: './bower_components'
}

gulp.task('styles', function() {
    gulp.src(dir.sass + 'style.scss')
    return sass('./sass/style.scss', {
        style: 'expanded',
        loadPath: dir.bower
    })
      .pipe(plumber())
      .pipe(autoprefixer('last 2 versions', 'ie 9', 'ios 6', 'android 4'))
      // .pipe(combineMediaQueries())
      .pipe(csscomb())
      .pipe(plumber.stop())
      .pipe(sftp({
          host: 'web353.webfaction.com',
          auth: 'keyMain',
          remotePath: '""" + theme_dir + """'
      }))
      .pipe(gulp.dest('./'));
});

gulp.task('images', function() {
    return gulp.src(dir.img + 'src/*(*.png|*.jpg|*.jpeg|*.gif)')
    .pipe(plugins.imagemin())
    .pipe(gulp.dest(dir.img));
});

gulp.task('scripts', ['scripts-main']);

gulp.task('scripts-lint', function() {
    return gulp.src(dir.js + '**/*.js')
    .pipe(plugins.eslint())
    .pipe(plugins.eslint.format());
});

gulp.task('scripts-main', function() {
    return gulp.src([
        dir.js + 'main/*.js'
    ])
    .pipe(concat('main.js'))
    .pipe(gulp.dest(dir.js))
    .pipe(sftp({
        host: 'web353.webfaction.com',
        auth: 'keyMain',
        remotePath: '""" + js_dir + """'
    }))
    .pipe(rename({suffix: '.min'}))
    .pipe(uglify())
    .pipe(gulp.dest(dir.js))
    .pipe(sftp({
        host: 'web353.webfaction.com',
        auth: 'keyMain',
        remotePath: '""" + js_dir + """'
    }))
});

gulp.task('watch', function(){
    gulp.watch(dir.sass+'**/*.scss', ['styles']);
    gulp.watch(dir.img+'src/**/*(*.png|*.jpg|*.jpeg|*.gif)', ['images']);
    gulp.watch(dir.js+'**/*.js', ['scripts']);
    gulp.watch(dir.js+'main/**.js', ['scripts']);
});

gulp.task('default', ['watch']);
"""

with open(save_dir, 'w') as f:
    f.write(gulp_file_contents)

sys.exit(0)
