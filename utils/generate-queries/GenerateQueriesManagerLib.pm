#!/usr/bin/perl

use warnings;
use strict;
use Encode;
use Carp;

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

### BEGIN INCLUDE Logger

# The package Logger is taken with permission from James Mayfield's ColdStart library

#####################################################################################
# Reporting Problems
#####################################################################################

# The following is the default list of problems that can be checked
# for. A different list of problems can be specified as an argument to
# Logger->new(). WARNINGs can be corrected and do not prevent further
# processing. ERRORs permit further error checking, but processing
# does not proceed after that. FATAL_ERRORs cause immediate program
# termination when the error is reported.

my $problem_formats = <<'END_PROBLEM_FORMATS';

# Error Name                    Type           Error Message
# ----------                    ----           -------------

########## General Errors
  MISSING_FILE                  FATAL_ERROR    Could not open %s: %s
  MISSING_KEY                   FATAL_ERROR    Missing key %s in container of type %s
  MISSING_ENCODING_FORMAT       FATAL_ERROR    Missing encoding format for document element %s

END_PROBLEM_FORMATS


#####################################################################################
# Logger
#####################################################################################

package Logger;

use Carp;

# Create a new Logger object
sub new {
  my ($class, $formats, $error_output) = @_;
  $formats = $problem_formats unless $formats;
  my $self = {FORMATS => {}, PROBLEMS => {}, PROBLEM_COUNTS => {}};
  bless($self, $class);
  $self->set_error_output($error_output);
  $self->add_formats($formats);
  $self;
}

# Add additional error formats to an existing Logger
sub add_formats {
  my ($self, $formats) = @_;
  # Convert the problem formats list to an appropriate hash
  chomp $formats;
  foreach (grep {/\S/} grep {!/^\S*#/} split(/\n/, $formats)) {
    s/^\s+//;
    my ($problem, $type, $format) = split(/\s+/, $_, 3);
    $self->{FORMATS}{$problem} = {TYPE => $type, FORMAT => $format};
  }
}

# Get a list of warnings that can be ignored through the -ignore switch
sub get_warning_names {
  my ($self) = @_;
  join(", ", grep {$self->{FORMATS}{$_}{TYPE} eq 'WARNING'} sort keys %{$self->{FORMATS}});
}

# Do not report warnings of the specified type
sub ignore_warning {
  my ($self, $warning) = @_;
  $self->NIST_die("Unknown warning: $warning") unless $self->{FORMATS}{$warning};
  $self->NIST_die("$warning is a fatal error; cannot ignore it") unless $self->{FORMATS}{$warning}{TYPE} eq 'WARNING';
  $self->{IGNORE_WARNINGS}{$warning}++;
}

# Just use the ignore_warning mechanism to delete errors, but don't enforce the warnings-only edict
sub delete_error {
  my ($self, $error) = @_;
  $self->NIST_die("Unknown error: $error") unless $self->{FORMATS}{$error};
  $self->{IGNORE_WARNINGS}{$error}++;
}

# Is a particular error being ignored?
sub is_ignored {
  my ($self, $warning) = @_;
  $self->NIST_die("Unknown error: $warning") unless $self->{FORMATS}{$warning};
  $self->{IGNORE_WARNINGS}{$warning};
}

# Remember that a particular problem was encountered, for later reporting
sub record_problem {
  my ($self, $problem, @args) = @_;
  my $source = pop(@args);
  # Warnings can be suppressed here; errors cannot
  return if $self->{IGNORE_WARNINGS}{$problem};
  my $format = $self->{FORMATS}{$problem} ||
               {TYPE => 'INTERNAL_ERROR',
		FORMAT => "Unknown problem $problem: %s"};
  $self->{PROBLEM_COUNTS}{$format->{TYPE}}++;
  my $type = $format->{TYPE};
  my $message = "$type: " . sprintf($format->{FORMAT}, @args);
  # Use Encode to support Unicode.
  $message = Encode::encode_utf8($message);
  my $where = (ref $source ? "$source->{FILENAME} line $source->{LINENUM}" : $source);
  $self->NIST_die("$message\n$where") if $type eq 'FATAL_ERROR' || $type eq 'INTERNAL_ERROR';
  $self->{PROBLEMS}{$problem}{$message}{$where}++;
}

# Send error output to a particular file or file handle
sub set_error_output {
  my ($self, $output) = @_;
  if (!$output) {
    $output = *STDERR{IO};
  }
  elsif (!ref $output) {
    if (lc $output eq 'stdout') {
      $output = *STDOUT{IO};
    }
    elsif (lc $output eq 'stderr') {
      $output = *STDERR{IO};
    }
    else {
      # $self->NIST_die("File $output already exists") if -e $output;
      open(my $outfile, ">:utf8", $output) or $self->NIST_die("Could not open $output: $!");
      $output = $outfile;
      $self->{OPENED_ERROR_OUTPUT} = 'true';
    }
  }
  $self->{ERROR_OUTPUT} = $output
}

# Retrieve the file handle for error output
sub get_error_output {
  my ($self) = @_;
  $self->{ERROR_OUTPUT};
}

# Close the error output if it was opened here
sub close_error_output {
  my ($self) = @_;
  close $self->{ERROR_OUTPUT} if $self->{OPENED_ERROR_OUTPUT};
}

# Report all of the problems that have been aggregated to the selected error output
sub report_all_problems {
  my ($self) = @_;
  my $error_output = $self->{ERROR_OUTPUT};
  foreach my $problem (sort keys %{$self->{PROBLEMS}}) {
    foreach my $message (sort keys %{$self->{PROBLEMS}{$problem}}) {
      my $num_instances = scalar keys %{$self->{PROBLEMS}{$problem}{$message}};
      print $error_output "$message";
      my $example = (sort keys %{$self->{PROBLEMS}{$problem}{$message}})[0];
      if ($example ne 'NO_SOURCE') {
	print $error_output " ($example";
	print $error_output " and ", $num_instances - 1, " other place" if $num_instances > 1;
	print $error_output "s" if $num_instances > 2;
	print $error_output ")";
      }
      print $error_output "\n\n";
    }
  }
  # Return the number of errors and the number of warnings encountered
  ($self->{PROBLEM_COUNTS}{ERROR} || 0, $self->{PROBLEM_COUNTS}{WARNING} || 0);
}

sub get_num_errors {
  my ($self) = @_;
  $self->{PROBLEM_COUNTS}{ERROR} || 0;
}

sub get_num_warnings {
  my ($self) = @_;
  $self->{PROBLEM_COUNTS}{WARNING} || 0;
}

sub get_error_type {
  my ($self, $error_name) = @_;
  $self->{FORMATS}{$error_name}{TYPE};
}

# NIST submission scripts demand an error code of 255 on failure
my $NIST_error_code = 255;

### DO NOT INCLUDE
# FIXME: Inconsistency: sometimes NIST_die is called directly; other
# times record_problem is called with a FATAL_ERROR
### DO INCLUDE
sub NIST_die {
  my ($self, @messages) = @_;
  my $outfile = $self->{ERROR_OUTPUT};
  print $outfile "================================================================\n";
  print $outfile Carp::longmess();
  print $outfile "================================================================\n";
  print $outfile join("", @messages), " at (", join(":", caller), ")\n";
  exit $NIST_error_code;
}

### END INCLUDE Logger

#####################################################################################
# LDCNISTMappings
#####################################################################################

package LDCNISTMappings;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = {
    CLASS => "LDCNISTMappings",
    PARAMETERS => $parameters,
    ROLE_MAPPINGS => {},
    TYPE_MAPPINGS => {},
    TYPE_CATEGORY => {},
    IS_VALID_ENTRYPOINT => {},
    LOGGER => $logger,
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

sub get_NIST_TYPE_CATEGORY {
	my ($self, $nist_type) = @_;

	$self->{TYPE_CATEGORY}{$nist_type};
}

sub is_valid_entrypoint {
	my ($self, $nist_type) = @_;

	$self->{IS_VALID_ENTRYPOINT}{$nist_type};
}

sub load_data {
	my ($self) = @_;
	my ($filename, $filehandler, $header, $entries, $i);
	
	# Load data from role mappings
	$filename = $self->get("PARAMETERS")->get("ROLE_MAPPING_FILE");
	$filehandler = FileHandler->new($self->get("LOGGER"), $filename);
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
  $filename = $self->get("PARAMETERS")->get("TYPE_MAPPING_FILE");
  $filehandler = FileHandler->new($self->get("LOGGER"), $filename);
  $header = $filehandler->get("HEADER");
  $entries = $filehandler->get("ENTRIES");
  $i=0;
  
  foreach my $entry( $entries->toarray() ){
    $i++;
    #print "ENTRY # $i:\n", $entry->tostring(), "\n";
    my $ldc_type = $entry->get("LDCTypeOutput");
    my $nist_type = $entry->get("NISTType");
    my $category = $entry->get("Category");
    my $is_valid_entrypoint = $entry->get("IsValidEntrypoint");

    $self->{TYPE_MAPPINGS}{$ldc_type} = $nist_type;  
    $self->{TYPE_CATEGORY}{$nist_type} = $category;
    $self->{IS_VALID_ENTRYPOINT}{$nist_type} = $is_valid_entrypoint;
  }
}

#####################################################################################
# DocumentIDsMappings
#####################################################################################

package DocumentIDsMappings;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = {
  	CLASS => "DocumentIDsMappings",
  	PARAMETERS => $parameters,
  	DOCUMENTS => Documents->new($logger),
    DOCUMENTELEMENTS => DocumentElements->new($logger),
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load_data();
  $self;
}

sub load_data {
	my ($self) = @_;
	
	# Load document-element to language mapping
	my %doceid_to_langs_mapping;
	my $filename = $self->get("PARAMETERS")->get("UID_INFO_FILE");
	my $filehandler = FileHandler->new($self->get("LOGGER"), $filename);
	my $header = $filehandler->get("HEADER");
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry($entries->toarray()) {
		my $doceid = $entry->get("derived_uid");
		my $languages = $entry->get("lang_manual");
		$doceid_to_langs_mapping{$doceid} = $languages;
	}
	
	# Load the DocumentIDsMappingsFile
	$filename = $self->get("PARAMETERS")->get("DOCUMENTIDS_MAPPING_FILE");

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
		my $documentelement = DocumentElement->new($self->get("LOGGER"));
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
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Document');
  $self->{CLASS} = 'Documents';
  $self->{LOGGER} = $logger;
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
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'DocumentElement');
  $self->{CLASS} = 'DocumentElements';
  $self->{LOGGER} = $logger;
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
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'DocumentElement');
  $self->{CLASS} = 'TheDocumentElements';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# Document
#####################################################################################

package Document;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $document_id) = @_;
  my $self = {
    CLASS => 'Document',
    DOCUMENTID => $document_id,
    DOCUMENTELEMENTS => DocumentElements->new($logger),
    LOGGER => $logger,
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
  my ($class, $logger) = @_;
  my $self = {
    CLASS => 'DocumentElement',
    DOCUMENT => undef,
    DOCUMENTID => undef,
    DOCUMENTELEMENTID => undef,
    TYPE => undef,
    LOGGER => $logger,
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
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Edge');
  $self->{CLASS} = 'Edges';
  $self->{EDGE_LOOKUP} = {};
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub add {
	my ($self, $value, $key) = @_;
	
	$self->SUPER::add($value, $key);
	push(@{$self->{EDGE_LOOKUP}{SUBJECT}{$value->get("SUBJECT_NODEID")}}, $value); 
	push(@{$self->{EDGE_LOOKUP}{OBJECT}{$value->get("OBJECT_NODEID")}}, $value); 
	push(@{$self->{EDGE_LOOKUP}{PREDICATE}{$value->get("PREDICATE")}}, $value);
	push(@{$self->{EDGE_LOOKUP}
								{"SUBJECT->OBJECT"}
								{$value->get("SUBJECT_NODEID")."->".$value->get("OBJECT_NODEID")}
								{$value->get("PREDICATE")}}, 
			$value);
}

#####################################################################################
# Edge
#####################################################################################

package Edge;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $subject, $nist_role, $object, $attribute) = @_;
  my $self = {
    CLASS => 'Edge',
    SUBJECT => $subject,
    PREDICATE => $nist_role,
    OBJECT => $object,
    ATTRIBUTE => $attribute,
    LOGGER => $logger,
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
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Node');
  $self->{CLASS} = 'Nodes';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# Node
#####################################################################################

package Node;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = {
    CLASS => 'Node',
    NODEID => undef,
    MENTIONS => Mentions->new($logger),
    LOGGER => $logger,
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

sub get_NIST_TYPE_CATEGORIES {
	my ($self) = @_;
	my %hash = map {$_=>1} map {$_->get("NIST_TYPE_CATEGORY")} $self->get("MENTIONS")->toarray();
	keys %hash;
}

sub has_compatible_types {
	my ($self) = @_;
	my @type_categories = grep {$_ ne "Filler"} $self->get("NIST_TYPE_CATEGORIES");
	return 0 if @type_categories > 1;
	return 1;
}

#####################################################################################
# Container
#####################################################################################

package Container;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $element_class) = @_;
  
  my $self = {
    CLASS => 'Container',
    ELEMENT_CLASS => $element_class,
    STORE => {},
    LOGGER => $logger,
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
    my $where = {FILENAME => __FILE__, LINENUM => __LINE__};
    $self->get("LOGGER")->record_problem("MISSING_KEY", $key, $self->get("ELEMENT_CLASS"), $where)
    	if $self->get("ELEMENT_CLASS") eq "RAW";
    my $element = $self->get("ELEMENT_CLASS")->new($self->get("LOGGER"));
    $self->add($element, $key);
  }
  $self->{STORE}{TABLE}{$key};
}

sub get_ALL_KEYS {
	my ($self) = @_;
	keys %{$self->{STORE}{TABLE}};
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
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Mention');
  $self->{CLASS} = 'Mentions';
  $self->{LOGGER} = $logger;
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
  my ($class, $logger) = @_;
  my $self = {
    CLASS => 'Mention',
    LDC_TYPE => undef, 
    NIST_TYPE => undef, 
    MENTIONID => undef,
    TREEID => undef,
    JUSTIFICATIONS => Justifications->new($logger),
    MODALITY => undef,
    LOGGER => $logger,
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

sub get_SPANS {
	my ($self) = @_;
	my $spans = Spans->new($self->get("LOGGER"));
	foreach my $justification($self->get("JUSTIFICATIONS")->toarray()) {
		foreach my $span($justification->get("SPANS")->toarray()) {
			$spans->add($span);
		}
	}
	$spans;
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
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Justification');
  $self->{CLASS} = 'Justifications';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# Justification
#####################################################################################

package Justification;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Spans');
  $self->{CLASS} = 'Justification';
  $self->{LOGGER} = $logger;
  $self->{SPANS} = Spans->new($self->get("LOGGER"));
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
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'Span');
  $self->{CLASS} = 'Spans';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# Span
#####################################################################################

package Span;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $documentid, $documenteid, $start, $end) = @_;
  $start = "nil" if $start eq "";
  $end = "nil" if $end eq "";
  my $self = {
    CLASS => 'Span',
    DOCUMENTID => $documentid,
    DOCUMENTEID => $documenteid,
    START => $start,
    END => $end,
    LOGGER => $logger,
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
  my ($class, $logger, $filename) = @_;
  my $self = {
    CLASS => 'FileHandler',
    FILENAME => $filename,
    HEADER => undef,
    ENTRIES => Container->new($logger),
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load($filename);
  $self;
}

sub load {
  my ($self, $filename) = @_;

  my $linenum = 0;

  open(FILE, $filename) or $self->get("LOGGER")->record_problem('MISSING_FILE', $filename, $!);
  my $line = <FILE>; 
  $line =~ s/\r\n?//g;
  chomp $line;

  $linenum++;

  $self->{HEADER} = Header->new($self->get("LOGGER"), $line);

  while($line = <FILE>){
    $line =~ s/\r\n?//g;
    $linenum++;
    chomp $line;
    my $entry = Entry->new($self->get("LOGGER"), $linenum, $line, $self->{HEADER}, 
    						{FILENAME => $filename, LINENUM => $linenum});
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
  my ($class, $logger, $line, $field_separator) = @_;
  $field_separator = "\t" unless $field_separator;
  my $self = {
    CLASS => 'Header',
    ELEMENTS => [],
    FIELD_SEPARATOR => $field_separator,
    LOGGER => $logger,
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
  my ($class, $logger, $linenum, $line, $header, $where, $field_separator) = @_;
  $field_separator = "\t" unless $field_separator;
  my $self = {
    CLASS => 'Entry',
    LINENUM => $linenum,
    LINE => $line,
    HEADER => $header,
    ELEMENTS => [],
    MAP => {},
    FIELD_SEPARATOR => $field_separator,
    WHERE => $where,
    LOGGER => $logger,
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

sub get_CATEGORY {
	my ($self) = @_;
	my $category = "n/a";
	$category = "ENTITY" if $self->get("entitymention_id");
	$category = "EVENT" if $self->get("eventmention_id");
	$category = "RELATION" if $self->get("relationmention_id");	
	$category;
}

sub get_nodemention_id {
	my ($self) = @_;
	my $nodemention_id;
	
	$nodemention_id = $self->get("entitymention_id") if $self->get("entitymention_id");
	$nodemention_id = $self->get("eventmention_id") if $self->get("eventmention_id");
	$nodemention_id = $self->get("relationmention_id") if $self->get("relationmention_id");
	$nodemention_id = $self->get("relation_event_mention_id") if $self->get("relation_event_mention_id");
	
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
  my ($class, $logger) = @_;
  my $self = {
    CLASS => 'DocumentElement',
    LOGGER => $logger,
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
  my ($class, $logger, $parameters) = @_;
  my $self = {
  	LDC_NIST_MAPPINGS => LDCNISTMappings->new($logger, $parameters),
  	NODES => Nodes->new($logger),
  	EDGES => Edges->new($logger),
  	DOCUMENTIDS_MAPPINGS => DocumentIDsMappings->new($logger, $parameters),
  	NODEIDS_LOOKUP => {},
    IMAGES_BOUNDINGBOXES => ImagesBoundingBoxes->new($logger, $parameters),
    KEYFRAMES_BOUNDINGBOXES => KeyFramesBoundingBoxes->new($logger, $parameters),
    ENCODINGFORMAT_TO_MODALITY_MAPPINGS => EncodingFormatToModalityMappings->new($logger, $parameters),
    PARAMETERS => $parameters,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self->load_data();
  foreach my $node($self->get("NODES")->toarray()) {
  	my $node_id = $node->get("NODEID");
  	my $node_types = join(",", $node->get("NIST_TYPES"));
  }
  $self;
}

sub get_DOCUMENTELEMENTS {
	my ($self) = @_;
	
	$self->get("DOCUMENTIDS_MAPPINGS")->get("DOCUMENTELEMENTS");
}

sub load_data {
	my ($self) = @_;

	$self->load_images_boundingboxes();
	$self->load_keyframes_boundingboxes();
	$self->load_nodes();
	$self->load_edges();
}

sub load_images_boundingboxes {
	my ($self) = @_;
	my $filehandler = FileHandler->new($self->get("LOGGER"), $self->get("PARAMETERS")->get("IMAGES_BOUNDINGBOXES_FILE"), $self->get("LOGGER"));
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry( $entries->toarray() ){
		$self->get("IMAGES_BOUNDINGBOXES")->add(ImageBoundingBox->new($self->get("LOGGER"), $entry->get("doceid"), $entry->get("type"),
												$entry->get("top_left_x"), $entry->get("top_left_y"),
												$entry->get("bottom_right_x"), $entry->get("bottom_right_y")),
								$entry->get("doceid"));
	}
}

sub load_keyframes_boundingboxes {
	my ($self) = @_;
	my $filehandler = FileHandler->new($self->get("LOGGER"), $self->get("PARAMETERS")->get("KEYFRAMES_BOUNDINGBOXES_FILE"));
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry( $entries->toarray() ){
		$self->get("KEYFRAMES_BOUNDINGBOXES")->add(KeyFrameBoundingBox->new($self->get("LOGGER"), $entry->get("keyframeid"),
												$entry->get("top_left_x"), $entry->get("top_left_y"),
												$entry->get("bottom_right_x"), $entry->get("bottom_right_y")),
								$entry->get("keyframeid"));
	}
}

sub load_edges {
	my ($self) = @_;
	my ($filehandler, $header, $entries, $i);
	foreach my $filename($self->get("PARAMETERS")->get("EDGES_DATA_FILES")->toarray()) {
		$filehandler = FileHandler->new($self->get("LOGGER"), $filename);
		$header = $filehandler->get("HEADER");
		$entries = $filehandler->get("ENTRIES");
		
		foreach my $entry( $entries->toarray() ){
			my $subject_node_id = $self->{NODEIDS_LOOKUP}{$entry->get("nodemention_id")};
			my $object_node_id = $self->{NODEIDS_LOOKUP}{$entry->get("arg_id")};
			# skip the edge unless you have both ids
			next unless ($subject_node_id && $object_node_id);
			my $subject = $self->get("NODES")->get("BY_KEY", $subject_node_id);
			my @subject_types = $subject->get("LDC_TYPES");
			my $slot_type = $entry->get("slot_type");
			my $attribute = $entry->get("attribute");
			my $object = $self->get("NODES")->get("BY_KEY", $object_node_id);
			
			foreach my $subject_type(@subject_types) {
				my $ldc_role = "$subject_type\_$slot_type";
				my $nist_role = $self->get("LDC_NIST_MAPPINGS")->get("NIST_ROLE", $ldc_role);
				next unless $nist_role;
				my $edge = Edge->new($self->get("LOGGER"), $subject, $nist_role, $object, $attribute);
				$self->get("EDGES")->add($edge);
			}
		}
	}
}

sub load_nodes {
	my ($self) = @_;
	my ($filehandler, $header, $entries, $i);
	
	# Load hypothesis file for information about relevant nodes
	my %acceptable_relevance = map {$_=>1} $self->get("PARAMETERS")->get("ACCEPTABLE_RELEVANCE")->toarray();
	my %nodementionids_relevant_to_hypotheses;
	my $filename = $self->get("PARAMETERS")->get("HYPOTHESES_FILE");
	$filehandler = FileHandler->new($self->get("LOGGER"), $filename);
	$header = $filehandler->get("HEADER");
	$entries = $filehandler->get("ENTRIES");
	foreach my $entry( $entries->toarray() ){
		my $nodemention_id = $entry->get("nodemention_id");
		my $relevance = $entry->get("value");
		next unless $acceptable_relevance{$relevance};
		$nodementionids_relevant_to_hypotheses{$nodemention_id} = 1;
	}
	
	# Load nodes relevant to hypothesis
	foreach my $filename($self->get("PARAMETERS")->get("NODES_DATA_FILES")->toarray()) {
		$filehandler = FileHandler->new($self->get("LOGGER"), $filename);
		$header = $filehandler->get("HEADER");
		$entries = $filehandler->get("ENTRIES"); 
		
		foreach my $entry( $entries->toarray() ){
			# skip the entry if the mention:
			#  (1) is a mention of an event or a relation
			#  (2) is not relevant to a hypotheses
			next if ($entry->get("CATEGORY") ne "ENTITY" && !$nodementionids_relevant_to_hypotheses{$entry->get("nodemention_id")});
			
			my $document_eid = $entry->get("provenance");
			my $thedocumentelement = $self->get("DOCUMENTELEMENTS")->get("BY_KEY", $document_eid);
			my $thedocumentelement_encodingformat = $thedocumentelement->get("TYPE");
			$self->get("LOGGER")->record_problem("MISSING_ENCODING_FORMAT", $document_eid, $entry->get("WHERE"));
			my $thedocumentelementmodality = $self->get("ENCODINGFORMAT_TO_MODALITY_MAPPINGS")->get("BY_KEY", 
																										$thedocumentelement_encodingformat);
			my $document_id = $thedocumentelement->get("DOCUMENTID");
			my $mention = Mention->new($self->get("LOGGER"));
			my $span = Span->new(
								$self->get("LOGGER"), 
								$entry->get("provenance"),
								$document_eid,
								$entry->get("textoffset_startchar"),
								$entry->get("textoffset_endchar"),
						);
			my $justification = Justification->new($self->get("LOGGER"));
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
			$mention->set("NIST_TYPE_CATEGORY",
							$self->get("LDC_NIST_MAPPINGS")->get("NIST_TYPE_CATEGORY",
								$mention->get("NIST_TYPE")));
			my $node = $self->get("NODES")->get("BY_KEY", $entry->get("kb_id"));

			$node->set("NODEID", $entry->get("kb_id")) unless $node->set("NODEID");
			$node->add_mention($mention);
			$self->{NODEIDS_LOOKUP}{$entry->get("document_level_node_id")} = $entry->get("kb_id");
			$self->{NODEIDS_LOOKUP}{$entry->get("nodemention_id")} = $entry->get("kb_id");
		}
	}
}

sub generate_queries {
	my ($self) = @_;
	
	$self->generate_class_queries();
	$self->generate_zerohop_queries();
	$self->generate_graph_queries();
}

sub generate_class_queries {
	my ($self) = @_;
	my $queries = ClassQueries->new($self->get("LOGGER"), $self->get("PARAMETERS"));
	my $query_id_prefix = $self->get("PARAMETERS")->get("CLASS_QUERIES_PREFIX");
	my $i = 0;
	my %type_category = %{$self->get("LDC_NIST_MAPPINGS")->get("TYPE_CATEGORY")};
	foreach my $type(keys %type_category) {
		my $category = $type_category{$type};
		if($category eq "Filler" or $category eq "Entity") {
			$i++;
			my $query_id = "$query_id_prefix\_$i";
			my $query = ClassQuery->new($self->get("LOGGER"), $query_id, $type);
			$queries->add($query);
		}
	}
	$queries->write_to_files();
}

sub generate_zerohop_queries {
	my ($self) = @_;
	my $queries = ZeroHopQueries->new($self->get("LOGGER"), $self->get("PARAMETERS"));
	my $query_id_prefix = $self->get("PARAMETERS")->get("ZEROHOP_QUERIES_PREFIX");
	my $i = 0;
	foreach my $node($self->get("NODES")->toarray()) {
		foreach my $mention($node->get("MENTIONS")->toarray()){
			my $enttype = $mention->get("NIST_TYPE");
			foreach my $span($mention->get("SPANS")->toarray()) {
				$i++;
				my $query_id = "$query_id_prefix\_$i";
				my $doceid = $span->get("DOCUMENTEID");
				my $start = $span->get("START");
				my $end = $span->get("END");
				my $modality = $mention->get("MODALITY");
				my $query = ZeroHopQuery->new($self->get("LOGGER"), $query_id, $enttype, $doceid, $modality, $start, $end);
				$queries->add($query);
			}
		}
	}	
	$queries->write_to_files();
}

sub generate_graph_queries {
	my ($self) = @_;
	my $queries = GraphQueries->new($self->get("LOGGER"), $self->get("PARAMETERS"));
	my $query_id_prefix = $self->get("PARAMETERS")->get("GRAPH_QUERIES_PREFIX");
	my $i = 0;
	foreach my $node(grep {$_->has_compatible_types()} $self->get("NODES")->toarray()) {
		# Get $edge1 and $edge2 such that:
		#   $node is the subject of $edge1, and
		#   $node is the object of $edge2.
		my %edge_lookup = %{$self->get("EDGES")->get("EDGE_LOOKUP")};
		foreach my $edge1(@{$edge_lookup{OBJECT}{$node->get("NODEID")} || []}) {
			foreach my $edge2(@{$edge_lookup{SUBJECT}{$node->get("NODEID")} || []}) {
				$i++;
				my $query_id = "$query_id_prefix\_$i";
				my $query = GraphQuery->new($self->get("LOGGER"), $self->get("DOCUMENTIDS_MAPPINGS"), $query_id, $edge1, $edge2);
				$query->add_entrypoint($node);
				$queries->add($query);
			}
		}
	}
	
	$queries->write_to_files();
}

#####################################################################################
# ImagesBoundingBoxes
#####################################################################################

package ImagesBoundingBoxes;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = $class->SUPER::new($logger, 'ImageBoundingBox');
  $self->{CLASS} = 'ImagesBoundingBoxes';
  $self->{PARAMETERS} = $parameters;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# ImageBoundingBox
#####################################################################################

package ImageBoundingBox;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $doceid, $type, $top_left_x, $top_left_y, $bottom_left_x, $bottom_left_y) = @_;
  my $self = {
    CLASS => 'ImageBoundingBox',
    DOCEID => $doceid,
    TYPE => $type,
    TOP_LEFT_X => $top_left_x,
    TOP_LEFT_Y => $top_left_y,
    BOTTOM_RIGHT_X => $bottom_left_x,
    BOTTOM_LEFT_Y => $bottom_left_y,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}


#####################################################################################
# KeyFramesBoundingBoxes
#####################################################################################

package KeyFramesBoundingBoxes;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = $class->SUPER::new($logger, 'KeyFrameBoundingBox');
  $self->{CLASS} = 'KeyFramesBoundingBoxes';
  $self->{PARAMETERS} = $parameters;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

#####################################################################################
# KeyFramesBoundingBox
#####################################################################################

package KeyFrameBoundingBox;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $keyframeid, $top_left_x, $top_left_y, $bottom_left_x, $bottom_left_y) = @_;
  my $self = {
    CLASS => 'KeyFrameBoundingBox',
    KEYFRAMEID => $keyframeid,
    TOP_LEFT_X => $top_left_x,
    TOP_LEFT_Y => $top_left_y,
    BOTTOM_RIGHT_X => $bottom_left_x,
    BOTTOM_LEFT_Y => $bottom_left_y,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_DOCEID {
	my ($self) = @_;

	my ($doceid) = split("_", $self->get("KEYFRAMEID"));
	$doceid;
}

#####################################################################################
# ClassQueries
#####################################################################################

package ClassQueries;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = $class->SUPER::new($logger, 'ClassQuery');
  $self->{CLASS} = 'ClassQueries';
  $self->{PARAMETERS} = $parameters;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub write_to_files {
	my ($self) = @_;
	my ($program_output_xml, $program_output_rq);
	my $output_filename_xml = $self->get("PARAMETERS")->get("CLASS_QUERIES_XML_OUTPUT_FILE");
	my $output_filename_rq = $self->get("PARAMETERS")->get("CLASS_QUERIES_RQ_OUTPUT_FILE");

	open($program_output_xml, ">:utf8", $output_filename_xml) or die("Could not open $output_filename_xml: $!");
	open($program_output_rq, ">:utf8", $output_filename_rq) or die("Could not open $output_filename_xml: $!");
	print $program_output_xml "<class_queries>\n";
	foreach my $query($self->toarray()) {
		$query->write_to_files($program_output_xml, $program_output_rq);
	}
	print $program_output_xml "<\/class_queries>\n";
	close($program_output_xml);
	close($program_output_rq);
}

#####################################################################################
# ClassQuery
#####################################################################################

package ClassQuery;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $query_id, $enttype) = @_;
  my $self = {
    CLASS => 'ClassQuery',
    QUERY_ID => $query_id,
    ENTTYPE => $enttype,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub write_to_files {
	my ($self, $program_output_xml, $program_output_rq) = @_;

	$self->write_to_xml($program_output_xml);
	$self->write_to_rq($program_output_rq);
}

sub write_to_xml {
	my ($self, $program_output) = @_;
	my $query_id = $self->get("QUERY_ID");
	my $enttype = $self->get("ENTTYPE");

	my $attributes = XMLAttributes->new($self->get("LOGGER"));
	$attributes->add("$query_id", "id");

	my $xml_enttype = XMLElement->new($self->get("LOGGER"), $enttype, "enttype", 0);
	my $xml_query = XMLElement->new($self->get("LOGGER"), $xml_enttype, "class_query", 1, $attributes);

	print $program_output $xml_query->tostring(2);
}

sub write_to_rq {
	my ($self, $program_output) = @_;
	my $query_id = $self->get("QUERY_ID");
	print $program_output "writing zerohop query to rq: $query_id\n";
}

#####################################################################################
# ZeroHopQueries
#####################################################################################

package ZeroHopQueries;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = $class->SUPER::new($logger, 'ZeroHopQuery');
  $self->{CLASS} = 'ZeroHopQueries';
  $self->{PARAMETERS} = $parameters;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub write_to_files {
	my ($self) = @_;
	my ($program_output_xml, $program_output_rq);
	my $output_filename_xml = $self->get("PARAMETERS")->get("ZEROHOP_QUERIES_XML_OUTPUT_FILE");
	my $output_filename_rq = $self->get("PARAMETERS")->get("ZEROHOP_QUERIES_RQ_OUTPUT_FILE");

	open($program_output_xml, ">:utf8", $output_filename_xml) or die("Could not open $output_filename_xml: $!");
	open($program_output_rq, ">:utf8", $output_filename_rq) or die("Could not open $output_filename_xml: $!");
	print $program_output_xml "<zerohop_queries>\n";
	foreach my $query($self->toarray()) {
		$query->write_to_files($program_output_xml, $program_output_rq);
	}
	print $program_output_xml "<\/zerohop_queries>\n";
	close($program_output_xml);
	close($program_output_rq);	
}

#####################################################################################
# ZeroHopQuery
#####################################################################################

package ZeroHopQuery;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $query_id, $enttype, $doceid, $modality, $start, $end) = @_;
  my $self = {
    CLASS => 'ZeroHopQuery',
    QUERY_ID => $query_id,
    ENTTYPE => $enttype,
    DOCUMENTELEMENTID => $doceid,
    MODALITY => $modality,
    START => $start,
    END => $end,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub write_to_files {
	my ($self, $program_output_xml, $program_output_rq) = @_;
	
	$self->write_to_xml($program_output_xml);
	$self->write_to_rq($program_output_rq);
}

sub write_to_xml {
	my ($self, $program_output) = @_;
	my $logger = $self->get("LOGGER");
	my $query_id = $self->get("QUERY_ID");
	my $enttype = $self->get("ENTTYPE");
	my $doceid = $self->get("DOCUMENTELEMENTID");
	my $modality = $self->get("MODALITY");
	my $start = $self->get("START");
	my $end = $self->get("END");

	my $xml_node = XMLElement->new($logger, "?node", "node", 0);
	my $xml_enttype = XMLElement->new($logger, $enttype, "enttype", 0);
	my $xml_doceid = XMLElement->new($logger, $doceid, "doceid", 0);
	my $xml_start = XMLElement->new($logger, $start, "start", 0);
	my $xml_end = XMLElement->new($logger, $end, "end", 0);
	my $xml_descriptor = XMLElement->new(
			$logger, 
			XMLContainer->new($logger, $xml_doceid, $xml_start, $xml_end),
			"descriptor",
			1);
	my $xml_entrypoint = XMLElement->new(
			$logger, 
			XMLContainer->new($logger, $xml_node, $xml_enttype, $xml_descriptor), 
			"entrypoint",
			1);
	my $attributes = XMLAttributes->new($logger);
	$attributes->add("$query_id", "id");
	my $xml_query = XMLElement->new($logger, $xml_entrypoint, "zerohop_query", 1, $attributes);
	print $program_output $xml_query->tostring(2);
}

sub write_to_rq {
	my ($self, $program_output) = @_;
	my $query_id = $self->get("QUERY_ID");
	print $program_output "writing zerohop query to rq: $query_id\n";
}


#####################################################################################
# GraphQueries
#####################################################################################

package GraphQueries;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger, $parameters) = @_;
  my $self = $class->SUPER::new($logger, 'GraphQuery');
  $self->{CLASS} = 'GraphQueries';
  $self->{PARAMETERS} = $parameters;
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub write_to_files {
	my ($self) = @_;
	my ($program_output_xml, $program_output_rq);
	my $output_filename_xml = $self->get("PARAMETERS")->get("GRAPH_QUERIES_XML_OUTPUT_FILE");
	my $output_filename_rq = $self->get("PARAMETERS")->get("GRAPH_QUERIES_RQ_OUTPUT_FILE");

	open($program_output_xml, ">:utf8", $output_filename_xml) or die("Could not open $output_filename_xml: $!");
	open($program_output_rq, ">:utf8", $output_filename_rq) or die("Could not open $output_filename_xml: $!");
	print $program_output_xml "<graph_queries>\n";
	foreach my $query($self->toarray()) {
		$query->write_to_files($program_output_xml, $program_output_rq);
	}
	print $program_output_xml "<\/graph_queries>\n";
	close($program_output_xml);
	close($program_output_rq);	
}

#####################################################################################
# GraphQuery
#####################################################################################

package GraphQuery;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $documentids_mappings, $query_id, @edges) = @_;
  my $self = {
    CLASS => 'GraphQuery',
    DOCUMENTIDS_MAPPINGS => $documentids_mappings,
    QUERY_ID => $query_id,
    EDGES => [@edges],
    ENTRYPOINTS => [],
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub add_entrypoint {
	my ($self, $node) = @_;
	push(@{$self->{ENTRYPOINTS}}, $node);
}

sub write_to_files {
	my ($self, $program_output_xml, $program_output_rq) = @_;
	
	$self->write_to_xml($program_output_xml);
	$self->write_to_rq($program_output_rq);
}

sub write_to_xml {
	my ($self, $program_output) = @_;
	my $logger = $self->get("LOGGER");
	my $query_id = $self->get("QUERY_ID");
	my $query_attributes = XMLAttributes->new($logger);
	$query_attributes->add("$query_id", "id");
	# process the edges into a graph
	my $xml_edges_container = XMLContainer->new($logger);
	my $edge_id = 0;
	foreach my $edge(@{$self->get("EDGES")}) {
		$edge_id++;
		my $subject = &mask($edge->get("SUBJECT")->get("NODEID"));
		my $object = &mask($edge->get("OBJECT")->get("NODEID"));
		my $predicate = $edge->get("PREDICATE");
		my $xml_subject = XMLElement->new($logger, $subject, "subject", 0);
		my $xml_object = XMLElement->new($logger, $object, "object", 0);
		my $xml_predicate = XMLElement->new($logger, $predicate, "predicate", 0);
		my $edge_predicate = XMLAttributes->new($logger);
		$edge_predicate->add("$edge_id", "id");
		my $xml_edge = XMLElement->new(
							$logger,
							XMLContainer->new($logger, $xml_subject, $xml_predicate, $xml_object),
							"edge",
							1,
							$edge_predicate);
		$xml_edges_container->add($xml_edge);
	}
	my $xml_edges = XMLElement->new($logger, $xml_edges_container, "edges", 1);
	my $xml_graph = XMLElement->new($logger, $xml_edges, "graph", 1);
	# process the entrypoints
	my $xml_entrypoints_container = XMLContainer->new($logger);
	foreach my $node(@{$self->get("ENTRYPOINTS")}) {
		my $node_id = &mask($node->get("NODEID"));
		my $xml_node = XMLElement->new($logger, $node_id, "node", 0);
		my $xml_entrypoint_container = XMLContainer->new($logger, $xml_node);
		foreach my $mention($node->get("MENTIONS")->toarray()){
			my $enttype = $mention->get("NIST_TYPE");
			my $xml_enttype = XMLElement->new($logger, $enttype, "enttype", 0);
			foreach my $span($mention->get("SPANS")->toarray()) {
				my $doceid = $span->get("DOCUMENTEID");
				my $start = $span->get("START");
				my $end = $span->get("END");
				my $modality = $self->get("DOCUMENTIDS_MAPPINGS")->get("DOCUMENTELEMENTS")->get("BY_KEY", $doceid)->get("TYPE");
				my $xml_doceid = XMLElement->new($logger, $doceid, "doceid", 0);
				my $xml_start = XMLElement->new($logger, $start, "start", 0);
				my $xml_end = XMLElement->new($logger, $end, "end", 0);
				my $xml_descriptor_container = XMLContainer->new($logger, $xml_enttype, $xml_doceid, $xml_start, $xml_end);
				my $xml_descriptor = XMLElement->new($logger, $xml_descriptor_container, "descriptor", 1);
				$xml_entrypoint_container->add($xml_descriptor);
			}
		}
		my $xml_entrypoint = XMLElement->new($logger, $xml_entrypoint_container, "entrypoint", 1);
		$xml_entrypoints_container->add($xml_entrypoint);
	}
	my $xml_entrypoints = XMLElement->new($logger, $xml_entrypoints_container, "entrypoints", 1);
	my $xml_query_container = XMLContainer->new($logger, $xml_graph, $xml_entrypoints);
	my $xml_query = XMLElement->new($logger, $xml_query_container, "graph_query", 1, $query_attributes);
	print $program_output $xml_query->tostring(2);
}

sub write_to_rq {
	my ($self, $program_output) = @_;
	my $query_id = $self->get("QUERY_ID");
	print $program_output "writing graph query to rq: $query_id\n";
}

sub mask {
	my ($input) = @_;

	"?$input";
}

#####################################################################################
# XMLAttributes
#####################################################################################

package XMLAttributes;

use parent -norequire, 'Container', 'Super';

sub new {
  my ($class, $logger) = @_;
  my $self = $class->SUPER::new($logger, 'XMLAttribute');
  $self->{CLASS} = 'XMLAttributes';
  $self->{LOGGER} = $logger;
  bless($self, $class);
  $self;
}

sub tostring {
	my ($self) = @_;
	my $retVal = " ";
	join (" ", map {"$_=\"".$self->get('BY_KEY', $_)."\""} ($self->get("ALL_KEYS")));
}

#####################################################################################
# XMLElement
#####################################################################################

package XMLElement;

use parent -norequire, 'Super';

sub new {
  my ($class, $logger, $element, $name, $newline, $attributes) = @_;
  my $self = {
    CLASS => 'XMLElement',
    NAME => $name,
    NEWLINE => $newline,
    ATTRIBUTES => $attributes,
    ELEMENT => $element,
    LOGGER => $logger,
  };
  bless($self, $class);
  $self;
}

sub get_OPENTAG {
	my ($self) = @_;
	
	my $attributes = "";
	$attributes = " " . $self->get("ATTRIBUTES")->tostring() if $self->get("ATTRIBUTES") ne "nil";
	
	"<" . $self->get("NAME") . $attributes . ">";
}

sub get_CLOSETAG {
	my ($self) = @_;
	
	"<\/" . $self->get("NAME") . ">";
}

sub tostring {
	my ($self, $indent) = @_;
	
	my $retVal = " " x $indent;
	$retVal .= $self->get("OPENTAG");
	$retVal .= "\n" if $self->get("NEWLINE");
	$retVal .= $self->get("ELEMENT")->tostring($indent+2) if ref $self->get("ELEMENT");
	$retVal .= " " . $self->get("ELEMENT") . " " unless ref $self->get("ELEMENT");
	$retVal .= " " x $indent if $self->get("NEWLINE");
	$retVal .= $self->get("CLOSETAG");
	$retVal .= "\n";
	
	$retVal;
}

#####################################################################################
# XMLContainer
#####################################################################################

package XMLContainer;

use parent -norequire, 'Container', 'Super';

sub new {
	my ($class, $logger, @xml_elements) = @_;
	my $self = $class->SUPER::new($logger, 'XMLElement');
	$self->{CLASS} = 'XMLContainer';
	$self->{LOGGER} = $logger;
	bless($self, $class);
	foreach my $xml_element(@xml_elements) {
		$self->add($xml_element);
	}
	$self;
}

sub tostring {
	my ($self, $indent) = @_;
	my $retVal = "";
	foreach my $xml_elements($self->toarray()) {
		$retVal .= $xml_elements->tostring($indent);
	}
	$retVal;
}

#####################################################################################
# EncodingFormatToModalityMappings
#####################################################################################

package EncodingFormatToModalityMappings;

use parent -norequire, 'Container', 'Super';

sub new {
	my ($class, $logger, $parameters) = @_;
	my $self = $class->SUPER::new($logger, 'RAW');
	$self->{CLASS} = 'EncodingFormatToModalityMappings';
	$self->{PARAMETERS} = $parameters;
	$self->{LOGGER} = $logger;
	bless($self, $class);
	$self->load_data();
	$self;
}

sub load_data {
	my ($self) = @_;
	my $filehandler = FileHandler->new($self->get("LOGGER"), $self->get("PARAMETERS")->get("ENCODINGFORMAT_TO_MODALITYMAPPING_FILE"));
	my $entries = $filehandler->get("ENTRIES");
	foreach my $entry($entries->toarray()) {
		my $encoding_format = $entry->get("encoding_format");
		my $modality = $entry->get("modality");
		$self->add($modality, $encoding_format);
	}
}

1;
