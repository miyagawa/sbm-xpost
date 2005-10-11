#!/ur/local/bin/perl
use strict;
use CGI;
use DateTime;
use HTTP::Request::Common;
use LWP::UserAgent;
use Template;
use XML::Atom::Entry;
use XML::Atom::Client;
use YAML;

(my $config = $ENV{SCRIPT_FILENAME}) =~ s/\.cgi$/.yaml/;
warn $config;
our $conf = YAML::LoadFile($config);

my $q = CGI->new;
if ($q->request_method eq 'POST') {
    do_post($q);
} else {
    do_form($q);
}

sub do_form {
    my $q = shift;
    print $q->header('text/html; charset=utf-8');
    binmode STDOUT, ":utf8";
    my $tt = Template->new;
    $tt->process(\<<TEMPLATE, { q => $q });
<html>
<head>
<title>del.icio.us and Hatena cross-poster</title>
<style>body { font-family: trebuchet MS, Arial; font-size: 13px }</style>
<body onload="document.forms[0].tags.focus()">
<h1>del.icio.us and Hatena cross-poster</h1>
<form action="[% q.url('-query'=>0) %]" method="post">
<table>
<tr><td style="text-align:right">URL:</td><td><input size="64" type="text" name="url" value="[% q.param('url')|html %]" /></td></tr>
<tr><td style="text-align:right">Title:</td><td><input size="64" type="text" name="title" value="[% q.param('title') | html %]" /></td></tr>
<tr><td style="text-align:right">Comment:</td><td><input size="64" type="text" name="comment" /></td></tr>
<tr><td style="text-align:right">Tags:</td><td><input size="64" type="text" name="tags" /></td></tr>
</table>
<input type="submit" value=" Save " />
</form>
<div><a href="javascript:location.href='[% q.url %]?url='+encodeURIComponent(location.href)+'&title='+encodeURIComponent(document.title)">bookmarklet</a></div>
</body>
TEMPLATE
    ;
}

sub do_post {
    my $q = shift;
    post_delicious($q);
    post_hatena($q);
    print $q->redirect($q->param('url'));
}

sub post_delicious {
    my $q = shift;
    my $url = URI->new("http://del.icio.us/api/posts/add");
    $url->query_form(
        url => $q->param('url'),
        description => $q->param('title'),
        extended => $q->param('comment'),
        tags => $q->param('tags'),
        dt   => DateTime->now,
    );
    my $ua = LWP::UserAgent->new;
    $ua->credentials("del.icio.us:80", "del.icio.us API", $conf->{delicious}->{username}, $conf->{delicious}->{password});
    my $res = $ua->get($url);
    warn $res->status_line unless $res->is_success;
}

sub post_hatena {
    my $q = shift;
    my $summary = join '', map "[$_]", split /\s+/, $q->param('tags');
    $summary .= " " . $q->param('comment') if $q->param('comment');

    my $entry = XML::Atom::Entry->new;
    my $link  = XML::Atom::Link->new;
    $link->rel('related');
    $link->type('text/html');
    $link->href($q->param('url'));
    $entry->add_link($link);
    $entry->summary($summary);

    my $client = XML::Atom::Client->new;
    $client->username($conf->{hatena}->{username});
    $client->password($conf->{hatena}->{password});
    $client->createEntry("http://b.hatena.ne.jp/atom/post", $entry)
        or warn $client->errstr;
}
