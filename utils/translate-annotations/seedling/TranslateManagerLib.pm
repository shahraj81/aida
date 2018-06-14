#!/usr/bin/perl

use warnings;
use strict;

#####################################################################################
# Root
#####################################################################################

package Super;

sub set {
  my ($self, $field, $value) = @_;
  my $method = $self->can("get_$field");
  $method->($self, $value) if $method;
  $self->{$field} = $value unless $method;
}

sub get {
	my ($self, $field, $arguments) = @_;
	return $self->{$field} if defined $self->{$field} && not defined $arguments;
	my $method = $self->can("get_$field");
	return $method->($self, $arguments) if $method;
	return "nil";
}

sub get_BY_INDEX {
  my ($self) = @_;
  die "Abstract method 'get_BY_INDEX' not defined in derived class '", $self->get("CLASS") ,"'\n";
}

sub get_BY_KEY {
	my ($self) = @_;
  die "Abstract method 'get_BY_KEY' not defined in derived class '", $self->get("CLASS") ,"'\n";
}

sub dump_structure {
  my ($structure, $label, $indent, $history, $skip) = @_;
  if (ref $indent) {
    $skip = $indent;
    undef $indent;
  }
  my $outfile = *STDERR;
  $indent = 0 unless defined $indent;
  $history = {} unless defined $history;

  # Handle recursive structures
  if ($history->{$structure}) {
    print $outfile "  " x $indent, "$label: CIRCULAR\n";
    return;
  }

  my $type = ref $structure;
  unless ($type) {
    $structure = 'undef' unless defined $structure;
    print $outfile "  " x $indent, "$label: $structure\n";
    return;
  }
  if ($type eq 'ARRAY') {
    $history->{$structure}++;
    print $outfile "  " x $indent, "$label:\n";
    for (my $i = 0; $i < @{$structure}; $i++) {
      &dump_structure($structure->[$i], $i, $indent + 1, $history, $skip);
    }
  }
  elsif ($type eq 'CODE') {
    print $outfile "  " x $indent, "$label: CODE\n";
  }
  elsif ($type eq 'IO::File') {
    print $outfile "  " x $indent, "$label: IO::File\n";
  }
  else {
    $history->{$structure}++;
    print $outfile "  " x $indent, "$label:\n";
    my %done;
  outer:
    # You can add field names prior to the sort to order the fields in a desired way
    foreach my $key (sort keys %{$structure}) {
      if ($skip) {
  foreach my $skipname (@{$skip}) {
    next outer if $key eq $skipname;
  }
      }
      next if $done{$key}++;
      # Skip undefs
      next unless defined $structure->{$key};
      &dump_structure($structure->{$key}, $key, $indent + 1, $history, $skip);
    }
  }
}

#####################################################################################
# Documents
#####################################################################################

package Documents;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class) = @_;
  my $self = $class->SUPER::new('Document');
  $self->{CLASS} = 'Documents';
  bless($self, $class);
  $self;
}

#####################################################################################
# DocumentElements
#    contains 'DocumentElement' across documents
#####################################################################################

package DocumentElements;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class) = @_;
  my $self = $class->SUPER::new('DocumentElement');
  $self->{CLASS} = 'DocumentElements';
  bless($self, $class);
  $self;
}

#####################################################################################
# TheDocumentElements
#    has 1+ 'DocumentElement' contained in the Document
#####################################################################################

package TheDocumentElements;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class) = @_;
  my $self = $class->SUPER::new('DocumentElement');
  $self->{CLASS} = 'TheDocumentElements';
  bless($self, $class);
  $self;
}

#####################################################################################
# Document
#####################################################################################

package Document;

use parent -norequire, 'Super';

sub new {
  my ($class, $document_id) = @_;
  my $self = {
    CLASS => 'Document',
    DOCUMENTID => $document_id,
    DOCUMENTELEMENTS => DocumentElements->new(),
  };
  bless($self, $class);
  $self;
}

sub add_document_element {
	my ($self, $document_element) = @_;
	$self->get("DOCUMENTELEMENTS")->add($document_element);
}

#####################################################################################
# DocumentElement
#####################################################################################

package DocumentElement;

use parent -norequire, 'Super';

sub new {
  my ($class) = @_;
  my $self = {
    CLASS => 'DocumentElement',
    DOCUMENT => undef,
    DOCUMENTID => undef,
    DOCUMENTELEMENTID => undef,
    TYPE => undef,
  };
  bless($self, $class);
  $self;
}

#####################################################################################
# Entities
#####################################################################################

package Entities;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class) = @_;
  my $self = $class->SUPER::new('Entity');
  $self->{CLASS} = 'Entities';
  bless($self, $class);
  $self;
}

#####################################################################################
# Entity
#####################################################################################

package Entity;

use parent -norequire, 'Super';

sub new {
	my ($class) = @_;
	my $self = {
		CLASS => 'Entity',
		NODEID => undef,
    MENTIONS => Mentions->new(),
    TYPE => undef,
    SUBTYPE => undef,
	};
	bless($self, $class);
	$self;
}

sub add_mention {
	my ($self, $mention) = @_;
	$self->get("MENTIONS")->add($mention);
}

sub tostring {
	my ($self) = @_;
	my $string = "";
	
}

#####################################################################################
# Container
#####################################################################################

package Container;

use parent -norequire, 'Super';

sub new {
	my ($class, $element_class) = @_;
	
	my $self = {
		CLASS => 'Container',
		ELEMENT_CLASS => $element_class,
		STORE => {},
	};
	bless($self, $class);
	$self;
}

sub get_BY_INDEX {
	my ($self, $index) = @_;
	$self->{STORE}{LIST}[$index];
}

sub get_BY_KEY {
	my ($self, $key) = @_;
	unless($self->{STORE}{TABLE}{$key}) {
		# Create an instance if not exists
		my $element = $self->get("ELEMENT_CLASS")->new();
		$self->add($element, $key);
	}
  $self->{STORE}{TABLE}{$key};
}

sub add {
	my ($self, $value, $key) = @_;
	push(@{$self->{STORE}{LIST}}, $value);
	$key = @{$self->{STORE}{LIST}} - 1 unless $key;
	$self->{STORE}{TABLE}{$key} = $value;
}

sub toarray {
  my ($self) = @_;
  @{$self->{STORE}{LIST} || []};
}

sub display {
	my ($self) = @_;
	print $self->tostring();
}

sub tostring {
	my ($self) = @_;
	my $string = "";
	foreach my $element( $self->toarray() ){
		$string .= $element->tostring();
		$string .= "\n";
	}
	$string;
}

#####################################################################################
# Mentions
#####################################################################################

package Mentions;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class) = @_;
  my $self = $class->SUPER::new('Mention');
  $self->{CLASS} = 'Mentions';
  bless($self, $class);
  $self;
}

#####################################################################################
# Mention
#####################################################################################

package Mention;

use parent -norequire, 'Super';

sub new {
  my ($class) = @_;
  my $self = {
  	CLASS => 'Mention',
  	# I don't think we need type here, the type should be associated with an entity
  	TYPE => undef, 
  	MENTIONID => undef,
  	TREEID => undef,
  	JUSTIFICATIONS => Justifications->new(),
  	MODALITY => undef,
  };
  bless($self, $class);
  $self;
}

sub add_justification {
  my ($self, $justification) = @_;
  $self->get("JUSTIFICATIONS")->add($justification);
}

sub get_SOURCE_DOCUMENTS {
	my ($self) = @_;
	my @source_docs;
	foreach my $justification($self->get("JUSTIFICATIONS")->toarray()) {
		foreach my $span($justification->get("SPANS")->toarray()) {
			push(@source_docs, $span->get("DOCUMENTID"));
		}
	}
	@source_docs;
}

sub get_SOURCE_DOCUMENT_ELEMENTS {
  my ($self) = @_;
  my @source_doces;
  foreach my $justification($self->get("JUSTIFICATIONS")->toarray()) {
    foreach my $span($justification->get("SPANS")->toarray()) {
      push(@source_doces, $span->get("DOCUMENTEID"));
    }
  }
  @source_doces;
}

#####################################################################################
# Justifications
#####################################################################################

package Justifications;

use parent -norequire, 'Container', 'Super';

sub new {
	my ($class) = @_;
	my $self = $class->SUPER::new('Justification');
	$self->{CLASS} = 'Justifications';
	bless($self, $class);
	$self;
}

#####################################################################################
# Justification
#####################################################################################

package Justification;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class) = @_;
  my $self = $class->SUPER::new('Spans');
  $self->{CLASS} = 'Justification';
  $self->{SPANS} = Spans->new();
  bless($self, $class);
  $self;
}

sub add_span {
  my ($self, $span) = @_;
  $self->get("SPANS")->add($span);
}

#####################################################################################
# Spans
#####################################################################################

package Spans;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class) = @_;
  my $self = $class->SUPER::new('Span');
  $self->{CLASS} = 'Spans';
  bless($self, $class);
  $self;
}

#####################################################################################
# Span
#####################################################################################

package Span;

use parent -norequire, 'Super';

sub new {
	my ($class, $documentid, $documenteid, $start, $end) = @_;
	my $self = {
		CLASS => 'Span',
		DOCUMENTID => $documentid,
		DOCUMENTEID => $documenteid,
		START => $start,
		END => $end,
	};
	bless($self, $class);
	$self;
}

#####################################################################################
# File Handler
#####################################################################################

package FileHandler;

use parent -norequire, 'Super';

sub new {
	my ($class, $filename) = @_;
	my $self = {
		CLASS => 'FileHandler',
		FILENAME => $filename,
		HEADER => undef,
		ENTRIES => Container->new(),
	};
	bless($self, $class);
	$self->load($filename);
	$self;
}

sub load {
	my ($self, $filename) = @_;

	my $linenum = 0;

	open(FILE, $filename);
	my $line = <FILE>; 
	$line =~ s/\r\n?//g;
	chomp $line;

	$linenum++;

	$self->{HEADER} = Header->new($line);

	while($line = <FILE>){
		$line =~ s/\r\n?//g;
		$linenum++;
		chomp $line;
		my $entry = Entry->new($linenum, $line, $self->{HEADER});
		$self->{ENTRIES}->add($entry);	
	}
	close(FILE);
}

sub display_header {
	my ($self) = @_;

	print $self->{HEADER}->tostring();	
}

sub display_entries {
	my ($self) = @_;

	print $self->{ENTRIES}->tostring();
}

sub display {
	my ($self) = @_;

	print "HEADER: \n";
	print $self->display_header();
	print "\n";
	print "ENTRIES: \n";
	print $self->display_entries();
	print "\n";	
}

#####################################################################################
# Header
#####################################################################################

package Header;

use parent -norequire, 'Super';

sub new {
	my ($class, $line, $field_separator) = @_;
	$field_separator = "\t" unless $field_separator;
	my $self = {
		CLASS => 'Header',
		ELEMENTS => [],
		FIELD_SEPARATOR => $field_separator,
	};
	bless($self, $class);
	$self->load($line);
	$self;
}

sub load {
	my ($self, $line) = @_;
	my $field_separator = $self->get("FIELD_SEPARATOR");
	@{$self->{ELEMENTS}} = split( /$field_separator/, $line);
}

sub get_NUM_OF_COLUMNS {
	my ($self) = @_;
	scalar @{$self->{ELEMENTS}};
}

sub get_ELEMENT_AT {
	my ($self, $at) = @_;

	$self->{ELEMENTS}[$at];
}

sub tostring {
	my ($self) = @_;
	my $i=0;
	my $string = "";
	my $num_of_columns = $self->get("NUM_OF_COLUMNS");
	foreach my $i( 0..$num_of_columns-1 ){
		 my $element = $self->get("ELEMENT_AT", $i);
		$string = $string ."$i . $element\n";
		$i++;
	}
	$string;
}

#####################################################################################
# Entry
#####################################################################################

package Entry;

use parent -norequire, 'Super';

sub new {
	my ($class, $linenum, $line, $header, $field_separator) = @_;
	$field_separator = "\t" unless $field_separator;
	my $self = {
		CLASS => 'Entry',
		LINENUM => $linenum,
		LINE => $line,
		HEADER => $header,
		ELEMENTS => [],
		MAP => {},
		FIELD_SEPARATOR => $field_separator,
	};
	bless($self, $class);
	$self->add($line, $header);
	$self;
}

sub get {
  my ($self, $field, $arguments) = @_;
  return $self->{$field} if defined $self->{$field} && not defined $arguments;
  return $self->{MAP}{$field} if defined $self->{MAP}{$field} && not defined $arguments;
  my $method = $self->can("get_$field");
  return $method->($self, $arguments) if $method;
  return;
}

sub add {
	my ($self, $line, $header) = @_;
	my $field_separator = $self->get("FIELD_SEPARATOR");
	@{$self->{ELEMENTS}} = split( /$field_separator/, $line);
	%{$self->{MAP}} = map {$header->get("ELEMENT_AT",$_) => $self->get("ELEMENT_AT",$_)} (0..$header->get("NUM_OF_COLUMNS")-1);
}

sub get_NUM_OF_COLUMNS {
	my ($self) = @_;
	scalar @{$self->{ELEMENTS}};
}

sub get_ELEMENT_AT {
	my ($self, $at) = @_;
	$self->{ELEMENTS}[$at];
}


sub tostring {
	my ($self) = @_;

	my $num_of_columns_header = $self->get("HEADER")->get("NUM_OF_COLUMNS");
	my $num_of_columns_entry  = $self->get("NUM_OF_COLUMNS");	

	die("Mismatching column numbers")
		if ($num_of_columns_header != $num_of_columns_entry);

	my $string = "";

	foreach my $i(0..$num_of_columns_entry-1) {
		$string = $string . $self->get("HEADER")->get("ELEMENT_AT", $i);
		$string = $string . ": "; 
		$string = $string . $self->get("ELEMENT_AT", $i);
		$string = $string . "\n";
	}

	$string;
}

1;
