import 'dart:convert';
import 'dart:ffi';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:flutter/material.dart';

class Post {
  int id;
  List<String> tags;
  double latitude;
  double longitude;
  File? imageFile;
  DateTime? date;
  int? poster;
  int? views;

  Post(
      {required this.id,
      required this.tags,
      required this.latitude,
      required this.longitude});

  Post.all(this.id, this.tags, this.latitude, this.longitude, this.imageFile,
      this.date, this.poster, this.views);

  @override
  String toString() {
    return "Post(id: $id, tags: $tags, latitude: $latitude, longitude: $longitude, imageFile: $imageFile, date: $date, poster: $poster, views: $views)";
  }
}

final String url =
    '192.168.1.66:5000'; //'192.168.1.84:5000';/*'162.156.55.214:5000';*/

// Get an image by the post ID
Future<Image> getImage(int postID) async {
  var request = Uri.http(url, 'posts/getImage', {'id': postID.toString()});
  var response = await http.get(request);
  if (response.statusCode == 200) {
    return Image.memory(base64Decode(response.body));
  } else {
    throw Exception(
        "Failed to get image for post $postID with error code ${response.statusCode}");
  }
}

// Upload a post to the database
Future<void> uploadPost(Post post) async {
  if (post.imageFile == null) {
    throw Exception("No image file was provided");
  }
  // var fileBytes = await post.imageFile!.openRead();
  var bytes = await post.imageFile!.readAsBytes();
  var image = http.MultipartFile.fromString('image', base64Encode(bytes));
  var uri = Uri.http(url, 'posts/uploadPost');
  var tags = json.encode(post.tags.map((e) => e.trim()).toList());
  var request = http.MultipartRequest("POST", uri)
    ..fields.addAll({
      'latitude': post.latitude.toString(),
      'longitude': post.longitude.toString(),
      'user': '1', // TODO user id
      'tags': tags,
    })
    ..files.add(image);
  var response = await request.send();
  if (response.statusCode == 400) {
    throw Exception("A parameter has been inputted incorrectly");
  } else if (response.statusCode != 200) {
    throw Exception("Failed to upload post");
  }
}

// Get all posts from the server. Optional arguments of tags, latitude,
// longitude, and radius can be passed in to filter the posts.
Future<List<Post>> getPosts(
    {int? pageNum,
    List<String>? tags,
    double? latitude,
    double? longitude,
    double? radius}) async {
  var queryParams = {
    "tags": tags,
    "latitude": latitude,
    "longitude": longitude,
    "radius": radius,
    "pageNum": pageNum.toString(),
  }..removeWhere((_, value) => value == null);
  var requestUrl = Uri.http(url, '/posts/getPosts', queryParams);
  var response = await http.get(requestUrl);
  if (response.statusCode == 200) {
    var json = jsonDecode(response.body);
    List<Post> posts = <Post>[];
    for (var v in json) {
      posts.add(Post.all(v["id"], v["tags"], v["latitude"], v["longitude"],
          null, DateTime.tryParse(v["date"]), v["poster"], v["views"]));
    }
    return posts;
  } else if (response.statusCode == 400) {
    throw Exception("A parameter has been inputted incorrectly");
  } else {
    throw Exception("Failed to get posts");
  }
}
