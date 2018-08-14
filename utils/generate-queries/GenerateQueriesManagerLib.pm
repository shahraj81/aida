#!/usr/bin/perl

use warnings;
use strict;

#####################################################################################
# Super
#####################################################################################

package Super;

sub set {
  my ($self, $field, $value) = @_;
  my $method = $self->can("get_$field");
  $method->($self, $value) if $method;
  $self->{$field} = $value unless $method;
}

sub get {
  my ($self, $field, @arguments) = @_;
  return $self->{$field} if defined $self->{$field} && not scalar @arguments;
  my $method = $self->can("get_$field");
  return $method->($self, @arguments) if $method;
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
# LDCNISTMappings
#####################################################################################

package LDCNISTMappings;

use parent -norequire, 'Super';

sub new {
  my ($class, $parameters) = @_;
  my $self = {
    CLASS => "LDCNISTMappings",
    PARAMETERS => $parameters,
    ROLE_MAPPINGS => {},
    TYPE_MAPPINGS => {},
    TYPE_CATEGORY => {},
  };
  bless($self, $class);
  $self->load_data();
  $self;
}

sub get_LDC_TYPE {
	my ($self, $type, $subtype) = @_;
	
	my $ldc_type = $type;
	$ldc_type = "$ldc_type.$subtype" if $subtype;
	
	$ldc_type;
}

sub get_NIST_TYPE {
	my ($self, $type, $subtype) = @_;
	
	my $key = $type;
	$key = "$key.$subtype" if $subtype;
	
	$self->{TYPE_MAPPINGS}{$key};
}

sub get_NIST_ROLE {
	my ($self, $ldc_role) = @_;
	
	$self->{ROLE_MAPPINGS}{$ldc_role};
}

sub load_data {
	my ($self) = @_;
	my ($filename, $filehandler, $header, $entries, $i);
	
	# Load data from role mappings
	$filename = $self->get("PARAMETERS")->get("RoleMappingFile");
	$filehandler = FileHandler->new($filename);
	$header = $filehandler->get("HEADER");
  $entries = $filehandler->get("ENTRIES");
  $i=0;

  foreach my $entry( $entries->toarray() ){
    $i++;
    #print "ENTRY # $i:\n", $entry->tostring(), "\n";
    my $category = $entry->get("category");
    my $ldc_type = $entry->get("ldctype");
    my $ldc_subtype = $entry->get("ldcsubtype");
    my $ldc_role = $entry->get("ldcrole");
    my $nist_type = $entry->get("nisttype");
    my $nist_subtype = $entry->get("nistsubtype");
    my $nist_role = $entry->get("nistrole");
  
    $self->{TYPE_MAPPINGS}{"$ldc_type.$ldc_subtype"} = "$nist_type.$nist_subtype";
    $self->{TYPE_CATEGORY}{"$nist_type.$nist_subtype"} = $category;
  
    my $ldc_fqrolename = "$ldc_type.$ldc_subtype\_$ldc_role";
    my $nist_fqrolename = "$nist_type.$nist_subtype\_$nist_role";
    $self->{ROLE_MAPPINGS}{$ldc_fqrolename} = $nist_fqrolename;
  }
  
  # Load data from type mappings
  $filename = $self->get("PARAMETERS")->get("TypeMappingFile");
  $filehandler = FileHandler->new($filename);
  $header = $filehandler->get("HEADER");
  $entries = $filehandler->get("ENTRIES");
  $i=0;
  
  foreach my $entry( $entries->toarray() ){
    $i++;
    #print "ENTRY # $i:\n", $entry->tostring(), "\n";
    my $ldc_type = $entry->get("LDCTypeOutput");
    my $nist_type = $entry->get("NISTType");
    my $category = $entry->get("Category");

    $self->{TYPE_MAPPINGS}{$ldc_type} = $nist_type;  
    $self->{TYPE_CATEGORY}{$nist_type} = $category;
  }
}

#####################################################################################
# DocumentIDsMappings
#####################################################################################

package DocumentIDsMappings;

use parent -norequire, 'Super';

sub new {
  my ($class, $parameters) = @_;
  my $self = {
  	CLASS => "DocumentIDsMappings",
  	PARAMETERS => $parameters,
  	DOCUMENTS => Documents->new(),
    DOCUMENTELEMENTS => DocumentElements->new(),
  };
  bless($self, $class);
  $self->load_data();
  $self;
}

sub load_data {
	my ($self) = @_;
	
	# Load document-element to language mapping
	my %doceid_to_langs_mapping;
	my $filename = $self->get("PARAMETERS")->get("UIDInfoFile");
	my $filehandler = FileHandler->new($filename);
	my $header = $filehandler->get("HEADER");
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry($entries->toarray()) {
		my $doceid = $entry->get("derived_uid");
		my $languages = $entry->get("lang_manual");
		$doceid_to_langs_mapping{$doceid} = $languages;
	}
	
	# Load the DocumentIDsMappingsFile
	$filename = $self->get("PARAMETERS")->get("DocumentIDsMappingsFile");
		
	open(my $infile, "<:utf8", $filename) or die("Could not open file: $filename");
  my $document_uri = "nil";
  my $uri = "nil";
  my %uri_to_id_mapping;
  my %doceid_to_docid_mapping;
  my %doceid_to_type_mapping;
	while(my $line = <$infile>) {
		chomp $line;
		if($line =~ /^\s*?(.*?)\s+.*?schema:DigitalDocument/i ) {
  		$uri = $1;
		}
    if($line =~ /schema:identifier\s+?\"(.*?)\".*?$/i) {
      my $id = $1;
      $uri_to_id_mapping{$uri} = $id;
    }
    if($line =~ /schema:encodingFormat\s+?\"(.*?)\".*?$/i) {
      my $type = $1;
      $doceid_to_type_mapping{$uri} = $type;
    }
    if($line =~ /schema:isPartOf\s+?(ldc:.*?)\s*?[.;]\s*?$/i) {
    	# $uri contains document_element_id
			$document_uri = $1;
			$doceid_to_docid_mapping{$uri} = $document_uri;
      $document_uri = "n/a";
      $uri = "n/a";
		}
	}
	close($infile);
	
	foreach my $document_element_uri(keys %doceid_to_docid_mapping) {
		my $document_uri = $doceid_to_docid_mapping{$document_element_uri};
		my $document_id = $uri_to_id_mapping{$document_uri};
    my $document_eid = $uri_to_id_mapping{$document_element_uri};
		my $detype = $doceid_to_type_mapping{$document_element_uri};
		my $delanguage = $doceid_to_langs_mapping{$document_eid};
		
    my $document = $self->get("DOCUMENTS")->get("BY_KEY", $document_id);
    $document->set("DOCUMENTID", $document_id);
    my $documentelement = DocumentElement->new();
    $documentelement->set("DOCUMENT", $document);
    $documentelement->set("DOCUMENTID", $document_id);
    $documentelement->set("DOCUMENTELEMENTID", $document_eid);
    $documentelement->set("LANGUAGES", $delanguage);
    $documentelement->set("TYPE", $detype);
    
    $document->add_document_element($documentelement);
    $self->get("DOCUMENTELEMENTS")->add($documentelement, $document_eid) unless $document_eid eq "n/a";
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
# Edges
#####################################################################################

package Edges;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class) = @_;
  my $self = $class->SUPER::new('Edge');
  $self->{CLASS} = 'Edges';
  $self->{EDGE_LOOKUP} = {};
  bless($self, $class);
  $self;
}

sub add {
	my ($self, $value, $key) = @_;
	
	$self->SUPER::add($value, $key);
	push(@{$self->{EDGE_LOOKUP}{SUBJECT}{$value->get("SUBJECT_NODEID")}}, $value); 
	push(@{$self->{EDGE_LOOKUP}{OBJECT}{$value->get("OBJECT_NODEID")}}, $value); 
	push(@{$self->{EDGE_LOOKUP}{PREDICATE}{$value->get("PREDICATE")}}, $value); 
}

#####################################################################################
# Edge
#####################################################################################

package Edge;

use parent -norequire, 'Super';

sub new {
  my ($class, $subject, $nist_role, $object, $attribute) = @_;
  my $self = {
    CLASS => 'Edge',
    SUBJECT => $subject,
    PREDICATE => $nist_role,
    OBJECT => $object,
    ATTRIBUTE => $attribute,
  };
  bless($self, $class);
  $self;
}

sub get_OBJECT_NODEID {
	my ($self) = @_;
	$self->get("OBJECT")->get("NODEID");
}

sub get_SUBJECT_NODEID {
	my ($self) = @_;
	$self->get("SUBJECT")->get("NODEID");
}

#####################################################################################
# Nodes
#####################################################################################

package Nodes;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class) = @_;
  my $self = $class->SUPER::new('Node');
  $self->{CLASS} = 'Nodes';
  bless($self, $class);
  $self;
}

#####################################################################################
# Node
#####################################################################################

package Node;

use parent -norequire, 'Super';

sub new {
  my ($class) = @_;
  my $self = {
    CLASS => 'Node',
    NODEID => undef,
    MENTIONS => Mentions->new(),
# NODE has no type ... its type is taken from its mentions
#    TYPE => undef,
  };
  bless($self, $class);
  $self;
}

sub add_mention {
  my ($self, $mention) = @_;
  $self->get("MENTIONS")->add($mention);
}

sub get_LDC_TYPES {
	my ($self) = @_;
	my %hash = map {$_=>1} map {$_->get("LDC_TYPE")} $self->get("MENTIONS")->toarray();
	keys %hash
}

sub get_NIST_TYPES {
	my ($self) = @_;
	my %hash = map {$_=>1} map {$_->get("NIST_TYPE")} $self->get("MENTIONS")->toarray();
	keys %hash;
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

sub get_MENTION {
  my ($self, $mention_id) = @_;
  my ($matching_mention) = grep {$_->{MENTIONID} eq $mention_id} $self->toarray();
  $matching_mention || "n/a";
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
    LDC_TYPE => undef, 
    NIST_TYPE => undef, 
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
  push (@source_docs, "nil") unless scalar @source_docs;
  @source_docs;
}

sub get_START {
  my ($self) = @_;
  my @starts;
  foreach my $justification($self->get("JUSTIFICATIONS")->toarray()) {
    foreach my $span($justification->get("SPANS")->toarray()) {
      push(@starts, $span->get("START"));
    }
  }
  push(@starts, "nil") unless scalar @starts;
  @starts;
}

sub get_END {
  my ($self) = @_;
  my @ends;
  foreach my $justification($self->get("JUSTIFICATIONS")->toarray()) {
    foreach my $span($justification->get("SPANS")->toarray()) {
      push(@ends, $span->get("END"));
    }
  }
  push(@ends, "nil") unless scalar @ends;
  @ends;
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
  $start = "nil" if $start eq "";
  $end = "nil" if $end eq "";
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
  my ($self, $field, @arguments) = @_;
  return $self->{$field} if defined $self->{$field} && not scalar @arguments;
  return $self->{MAP}{$field} if defined $self->{MAP}{$field} && not scalar @arguments;
  my $method = $self->can("get_$field");
  return $method->($self, @arguments) if $method;
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

sub get_nodemention_id {
	my ($self) = @_;
	my $nodemention_id;
	
	$nodemention_id = $self->get("entitymention_id") if $self->get("entitymention_id");
	$nodemention_id = $self->get("eventmention_id") if $self->get("eventmention_id");
	$nodemention_id = $self->get("relationmention_id") if $self->get("relationmention_id");
	
	$nodemention_id;
}

sub get_document_level_node_id {
	my ($self) = @_;
	my $node_id;
	
	$node_id = $self->get("entity_id") if $self->get("entity_id");
	$node_id = $self->get("event_id") if $self->get("event_id");
	$node_id = $self->get("relation_id") if $self->get("relation_id");
	
	$node_id;
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

#####################################################################################
# Parameters
#####################################################################################

package Parameters;

use parent -norequire, 'Super';

sub new {
  my ($class) = @_;
  my $self = {
    CLASS => 'DocumentElement',
  };
  bless($self, $class);
  $self;
}

#####################################################################################
# Graph
#####################################################################################

package Graph;

use parent -norequire, 'Super';

sub new {
  my ($class, $parameters) = @_;
  my $self = {
  	LDC_NIST_MAPPINGS => LDCNISTMappings->new($parameters),
  	NODES => Nodes->new(),
  	EDGES => Edges->new(),
  	DOCUMENTIDS_MAPPINGS => DocumentIDsMappings->new($parameters),
  	NODEIDS_LOOKUP => {},
    PARAMETERS => $parameters,
  };
  bless($self, $class);
  $self->load_data();
  foreach my $node($self->get("NODES")->toarray()) {
  	my $node_id = $node->get("NODEID");
  	my $node_types = join(",", $node->get("NIST_TYPES"));
  	print "==>$node_id $node_types\n";
  }
  $self;
}

sub get_DOCUMENTELEMENTS {
	my ($self) = @_;
	
	$self->get("DOCUMENTIDS_MAPPINGS")->get("DOCUMENTELEMENTS");
}

sub load_data {
	my ($self) = @_;

	$self->load_nodes();
	$self->load_edges();
}

sub load_edges {
	my ($self) = @_;
	my ($filehandler, $header, $entries, $i);
	foreach my $filename($self->get("PARAMETERS")->get("EDGES_DATA_FILES")->toarray()) {
		$filehandler = FileHandler->new($filename);
		$header = $filehandler->get("HEADER");
		$entries = $filehandler->get("ENTRIES");
		$i=0;
		
		foreach my $entry( $entries->toarray() ){
			$i++;
			#print "ENTRY # $i:\n", $entry->tostring(), "\n";
			my $subject_node_id = $self->{NODEIDS_LOOKUP}{$entry->get("nodemention_id")};
			my $subject = $self->get("NODES")->get("BY_KEY", $subject_node_id);
			my @subject_types = $subject->get("LDC_TYPES");
			my $slot_type = $entry->get("slot_type");
			my $attribute = $entry->get("attribute");
			my $object_node_id = $self->{NODEIDS_LOOKUP}{$entry->get("arg_id")};
			my $object = $self->get("NODES")->get("BY_KEY", $object_node_id);
			
			foreach my $subject_type(@subject_types) {
				my $ldc_role = "$subject_type\_$slot_type";
				my $nist_role = $self->get("LDC_NIST_MAPPINGS")->get("NIST_ROLE", $ldc_role);
				next unless $nist_role;
				my $edge = Edge->new($subject, $nist_role, $object, $attribute);
				$self->get("EDGES")->add($edge);
			}
		}
	}
}

sub load_nodes {
	my ($self) = @_;
	my ($filehandler, $header, $entries, $i);
	foreach my $filename($self->get("PARAMETERS")->get("NODES_DATA_FILES")->toarray()) {
		$filehandler = FileHandler->new($filename);
		$header = $filehandler->get("HEADER");
		$entries = $filehandler->get("ENTRIES"); 
		$i=0;
		
		foreach my $entry( $entries->toarray() ){
			$i++;
			#print "ENTRY # $i:\n", $entry->tostring(), "\n";
			my $document_eid = $entry->get("provenance");
			my $thedocumentelement = $self->get("DOCUMENTELEMENTS")->get("BY_KEY", $document_eid);
			my $thedocumentelementmodality = $thedocumentelement->get("TYPE");
			my $document_id = $thedocumentelement->get("DOCUMENTID");
			my $mention = Mention->new();
			my $span = Span->new(
								$entry->get("provenance"),
								$document_eid,
								$entry->get("textoffset_startchar"),
								$entry->get("textoffset_endchar"),
						);
			my $justification = Justification->new();
			$justification->add_span($span);
			$mention->add_justification($justification);
			$mention->set("MODALITY", $thedocumentelementmodality);
			$mention->set("MENTIONID", $entry->get("nodemention_id"));
			$mention->set("DOC_NODEID", $entry->get("document_level_node_id"));
			$mention->set("TEXT_STRING", $entry->get("text_string"));
			$mention->set("JUSTIFICATION_STRING", $entry->get("justification"));
			$mention->set("TREEID", $entry->get("tree_id"));
			
			$mention->set("LDC_TYPE", 
							$self->get("LDC_NIST_MAPPINGS")->get("LDC_TYPE", 
								$entry->get("type"), 
								$entry->get("subtype")));
			$mention->set("NIST_TYPE", 
							$self->get("LDC_NIST_MAPPINGS")->get("NIST_TYPE", 
								$entry->get("type"), 
								$entry->get("subtype")));

			my $node = $self->get("NODES")->get("BY_KEY", $entry->get("kb_id"));

			$node->set("NODEID", $entry->get("kb_id")) unless $node->set("NODEID");
			$node->add_mention($mention);
			$self->{NODEIDS_LOOKUP}{$entry->get("document_level_node_id")} = $entry->get("kb_id");
			$self->{NODEIDS_LOOKUP}{$entry->get("nodemention_id")} = $entry->get("kb_id");
			
# NODE has no type ... its type is taken from its mentions
#			$node->set("TYPE", $self->get("LDC_NIST_MAPPINGS")->get("NIST_TYPE", 
#																													$entry->get("type"), 
#																													$entry->get("subtype"))) 
#									unless $node->set("TYPE");			
		}
	}
}

1;
