#!/usr/bin/perl

use warnings;
use strict;

#####################################################################################
# File Handler
#####################################################################################

package FileHandler;

sub new {
	my ($class, $filename) = @_;
	my $self = { 
		FILENAME => $filename,
		HEADER => undef,
		ENTRIES => ListContainer->new(),
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
		$self->{ENTRIES}->push($entry);	
	}
	close(FILE);
}

sub get {
    my ($self, $field, $arguments) = @_;
    return $self->{$field} if defined $self->{$field} && not defined $arguments;
    my $method = $self->can("get_$field");
    return $method->($self, $arguments) if $method;
    return;
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

sub new {
	my ($class, $line, $field_separator) = @_;
	$field_separator = "\t" unless $field_separator;
	my $self = {
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

sub get {
	my ($self, $field, $arguments) = @_;
	return $self->{$field} if defined $self->{$field} && not defined $arguments;
	my $method = $self->can("get_$field");
	return $method->($self, $arguments) if $method;
	return;
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

sub new {
	my ($class, $linenum, $line, $header, $field_separator) = @_;
	$field_separator = "\t" unless $field_separator;
	my $self = {
		LINENUM => $linenum,
		HEADER => $header,
		ELEMENTS => [],
		MAP => {},
		FIELD_SEPARATOR => $field_separator,
	};
	bless($self, $class);
	$self->add($line, $header);
	$self;
}

sub add {
	my ($self, $line, $header) = @_;
	my $field_separator = $self->get("FIELD_SEPARATOR");
	@{$self->{ELEMENTS}} = split( /$field_separator/, $line);
	$self->{MAP} = map {$header->get("ELEMENT_AT",$_) => $self->get("ELEMENT_AT",$_)} (0..$header->get("NUM_OF_COLUMNS")-1);
}

sub get {
	my ($self, $field, $arguments) = @_;
	return $self->{$field} if defined $self->{$field} && not defined $arguments;
	my $method = $self->can("get_$field");
	return $method->($self, $arguments) if $method;
	return;
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

#####################################################################################
# ListContainer
#####################################################################################

package ListContainer;

sub new {
	my ($class) = @_;
	my $self = {
					CONTAINER => [],
			};
	bless($self, $class);
	$self;
};

sub push {
	my ($self, $element) = @_;

	push(@{$self->{CONTAINER}}, $element);
}

sub pop {
	my ($self, $element) = @_;

	pop(@{$self->{CONTAINER}});
}

sub get {
	my ($self, $field, $arguments) = @_;
	return $self->{$field} if defined $self->{$field} && not defined $arguments;
	my $method = $self->can("get_$field");
	return $method->($self, $arguments) if $method;
	return;
}

sub get_ENTRY_AT {
	my ($self, $at) = @_;
	$self->{CONTAINER}[$at];
}

sub get_NUM_OF_ENTRIES {
	my ($self) = @_;
	scalar @{$self->{CONTAINER}};
}

sub tostring {
	my ($self) = @_;
	my $string = "";
	foreach my $element(@{$self->{CONTAINER}}) {
		$string = $string . $element->tostring();
	}
	$string;
}


1;
